from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.schemas import (
    EstablishmentCreate, EstablishmentUpdate, EstablishmentResponse,
    UserResponse, EstablishmentSearchParams
)
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user, get_current_owner, verify_establishment_owner

router = APIRouter(prefix="/establishments", tags=["Establishments"])


@router.get("", response_model=List[EstablishmentResponse])
async def list_establishments(
    city: Optional[str] = None,
    category: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = Query(10.0, ge=0.1, le=100),
    limit: int = Query(50, ge=1, le=100)
):
    """List establishments with optional filters."""
    supabase = get_supabase()
    
    query = supabase.table("establishments").select("*").eq("is_active", True)
    
    if city:
        query = query.ilike("city", f"%{city}%")
    
    if category:
        query = query.eq("category", category)
    
    query = query.limit(limit)
    
    response = query.execute()
    
    establishments = [EstablishmentResponse(**item) for item in response.data]
    
    # Calculate distance if coordinates provided
    if latitude is not None and longitude is not None:
        from geopy.distance import geodesic
        
        for establishment in establishments:
            distance = geodesic(
                (latitude, longitude),
                (establishment.latitude, establishment.longitude)
            ).kilometers
            establishment.distance_km = round(distance, 2)
        
        # Filter by radius and sort by distance
        establishments = [e for e in establishments if e.distance_km <= radius_km]
        establishments.sort(key=lambda x: x.distance_km)
    
    return establishments


@router.get("/nearest", response_model=List[EstablishmentResponse])
async def get_nearest_establishments(
    latitude: float,
    longitude: float,
    radius_km: float = Query(10.0, ge=0.1, le=100),
    limit: int = Query(20, ge=1, le=50)
):
    """Get nearest establishments to a location."""
    supabase = get_supabase()
    
    # Use PostGIS for efficient spatial query
    # Note: This requires raw SQL or using PostgREST's advanced features
    # For simplicity, we'll fetch all and filter in Python (use PostGIS in production)
    
    query = supabase.table("establishments").select("*").eq("is_active", True).limit(limit * 3)
    response = query.execute()
    
    from geopy.distance import geodesic
    
    establishments = []
    for item in response.data:
        distance = geodesic(
            (latitude, longitude),
            (item["latitude"], item["longitude"])
        ).kilometers
        
        if distance <= radius_km:
            establishment = EstablishmentResponse(**item)
            establishment.distance_km = round(distance, 2)
            establishments.append(establishment)
    
    # Sort by distance and limit
    establishments.sort(key=lambda x: x.distance_km)
    return establishments[:limit]


@router.get("/{establishment_id}", response_model=EstablishmentResponse)
async def get_establishment(establishment_id: str):
    """Get a single establishment by ID."""
    supabase = get_supabase()
    
    response = supabase.table("establishments").select("*").eq("id", establishment_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )
    
    return EstablishmentResponse(**response.data[0])


@router.post("", response_model=EstablishmentResponse, status_code=status.HTTP_201_CREATED)
async def create_establishment(
    establishment_data: EstablishmentCreate,
    current_user: UserResponse = Depends(get_current_owner)
):
    """Create a new establishment (owner only)."""
    supabase = get_supabase()
    
    # Prepare data for insertion
    data = establishment_data.model_dump()
    data["owner_id"] = current_user.id
    
    try:
        response = supabase.table("establishments").insert(data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create establishment"
            )
        
        return EstablishmentResponse(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create establishment: {str(e)}"
        )


@router.put("/{establishment_id}", response_model=EstablishmentResponse)
async def update_establishment(
    establishment_id: str,
    establishment_update: EstablishmentUpdate,
    current_user: UserResponse = Depends(get_current_owner)
):
    """Update an establishment (owner only)."""
    supabase = get_supabase()
    
    # Verify ownership
    establishment_response = supabase.table("establishments").select("owner_id").eq("id", establishment_id).execute()
    
    if not establishment_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )
    
    verify_establishment_owner(establishment_response.data[0]["owner_id"], current_user)
    
    # Update establishment
    update_data = establishment_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to update"
        )
    
    try:
        response = supabase.table("establishments").update(update_data).eq("id", establishment_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed"
            )
        
        return EstablishmentResponse(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/{establishment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_establishment(
    establishment_id: str,
    current_user: UserResponse = Depends(get_current_owner)
):
    """Delete an establishment (owner only)."""
    supabase = get_supabase()
    
    # Verify ownership
    establishment_response = supabase.table("establishments").select("owner_id").eq("id", establishment_id).execute()
    
    if not establishment_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )
    
    verify_establishment_owner(establishment_response.data[0]["owner_id"], current_user)
    
    # Delete establishment
    try:
        supabase.table("establishments").delete().eq("id", establishment_id).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delete failed: {str(e)}"
        )


@router.get("/{establishment_id}/spaces", response_model=List)
async def get_establishment_spaces(establishment_id: str):
    """Get all spaces for an establishment."""
    supabase = get_supabase()
    
    # First verify establishment exists
    est_response = supabase.table("establishments").select("id").eq("id", establishment_id).execute()
    if not est_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )
    
    # Get spaces
    response = supabase.table("spaces").select("*").eq("establishment_id", establishment_id).execute()
    
    return response.data


@router.get("/search/advanced", response_model=List[EstablishmentResponse])
async def advanced_search(
    q: Optional[str] = None,  # General search query
    category: Optional[str] = None,
    city: Optional[str] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    services: Optional[str] = None,  # Comma-separated
    open_now: Optional[bool] = None,
    available_now: Optional[bool] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = Query(50.0, ge=0.1, le=200),
    limit: int = Query(50, ge=1, le=100)
):
    """Advanced search with multiple filters."""
    supabase = get_supabase()
    
    query = supabase.table("establishments").select("*").eq("is_active", True)
    
    # Text search
    if q:
        query = query.or_(f"name.ilike.%{q}%,description.ilike.%{q}%,address.ilike.%{q}%")
    
    # Category filter
    if category:
        query = query.eq("category", category)
    
    # City filter
    if city:
        query = query.ilike("city", f"%{city}%")
    
    # Rating filter
    if min_rating is not None:
        query = query.gte("rating", min_rating)
    
    query = query.limit(limit * 2)  # Fetch more for post-filtering
    response = query.execute()
    
    establishments = []
    
    for item in response.data:
        establishment = EstablishmentResponse(**item)
        
        # Services filter
        if services:
            required_services = [s.strip() for s in services.split(",")]
            establishment_services = item.get("services", []) or []
            if not all(service in establishment_services for service in required_services):
                continue
        
        # Open now filter (simplified - would need opening_hours in DB)
        if open_now:
            # TODO: Implement with actual opening hours
            pass
        
        # Available now filter
        if available_now:
            # Check if any space is available right now
            from datetime import datetime
            now = datetime.utcnow()
            spaces_response = supabase.table("spaces")\
                .select("id")\
                .eq("establishment_id", item["id"])\
                .eq("is_available", True)\
                .execute()
            
            if not spaces_response.data:
                continue
            
            # Check for active reservations
            has_available = False
            for space in spaces_response.data:
                reservations = supabase.table("reservations")\
                    .select("id")\
                    .eq("space_id", space["id"])\
                    .in_("status", ["pending", "confirmed"])\
                    .lte("start_time", now.isoformat())\
                    .gte("end_time", now.isoformat())\
                    .execute()
                
                if len(reservations.data) == 0:
                    has_available = True
                    break
            
            if not has_available:
                continue
        
        # Distance calculation
        if latitude is not None and longitude is not None:
            from geopy.distance import geodesic
            distance = geodesic(
                (latitude, longitude),
                (establishment.latitude, establishment.longitude)
            ).kilometers
            establishment.distance_km = round(distance, 2)
            
            if establishment.distance_km > radius_km:
                continue
        
        establishments.append(establishment)
    
    # Sort by distance if coordinates provided, otherwise by rating
    if latitude is not None and longitude is not None:
        establishments.sort(key=lambda x: x.distance_km)
    else:
        establishments.sort(key=lambda x: x.rating, reverse=True)
    
    return establishments[:limit]
