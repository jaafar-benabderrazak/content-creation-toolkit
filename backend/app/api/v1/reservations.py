from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.schemas import (
    ReservationCreate, ReservationResponse, ReservationUpdate,
    CheckInRequest, UserResponse, ReservationStatus
)
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user, get_current_owner
from app.core.config import settings

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.get("", response_model=List[ReservationResponse])
async def list_user_reservations(
    status_filter: Optional[ReservationStatus] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """List current user's reservations."""
    supabase = get_supabase()
    
    query = supabase.table("reservations").select("*").eq("user_id", current_user.id).order("start_time", desc=True)
    
    if status_filter:
        query = query.eq("status", status_filter.value)
    
    response = query.execute()
    
    return [ReservationResponse(**item) for item in response.data]


@router.get("/establishment/{establishment_id}", response_model=List[ReservationResponse])
async def list_establishment_reservations(
    establishment_id: str,
    current_user: UserResponse = Depends(get_current_owner)
):
    """List reservations for an establishment (owner only)."""
    supabase = get_supabase()
    
    # Verify ownership
    est_response = supabase.table("establishments").select("owner_id").eq("id", establishment_id).execute()
    
    if not est_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )
    
    if est_response.data[0]["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these reservations"
        )
    
    # Get reservations
    response = supabase.table("reservations").select("*").eq("establishment_id", establishment_id).order("start_time", desc=False).execute()
    
    return [ReservationResponse(**item) for item in response.data]


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a single reservation."""
    supabase = get_supabase()
    
    response = supabase.table("reservations").select("*").eq("id", reservation_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    reservation = response.data[0]
    
    # Verify user owns this reservation or owns the establishment
    if reservation["user_id"] != current_user.id:
        # Check if user owns the establishment
        est_response = supabase.table("establishments").select("owner_id").eq("id", reservation["establishment_id"]).execute()
        if not est_response.data or est_response.data[0]["owner_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this reservation"
            )
    
    return ReservationResponse(**reservation)


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    reservation_data: ReservationCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new reservation."""
    supabase = get_supabase()
    
    # Validate space exists and get establishment_id
    space_response = supabase.table("spaces").select("id, establishment_id, is_available").eq("id", reservation_data.space_id).execute()
    
    if not space_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    space = space_response.data[0]
    
    if not space["is_available"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Space is not available"
        )
    
    # Calculate cost
    duration_hours = (reservation_data.end_time - reservation_data.start_time).total_seconds() / 3600
    cost_credits = max(
        settings.MIN_CREDIT_COST,
        min(settings.MAX_CREDIT_COST, int(duration_hours * settings.CREDIT_COST_PER_HOUR))
    )
    
    # Check user has enough credits
    if current_user.coffee_credits < cost_credits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. Need {cost_credits}, have {current_user.coffee_credits}"
        )
    
    # Check availability (no overlapping reservations)
    overlap_check = supabase.rpc(
        "check_space_availability",
        {
            "p_space_id": reservation_data.space_id,
            "p_start_time": reservation_data.start_time.isoformat(),
            "p_end_time": reservation_data.end_time.isoformat()
        }
    ).execute()
    
    if not overlap_check.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Space is not available for the selected time"
        )
    
    # Create reservation
    try:
        data = reservation_data.model_dump()
        data["user_id"] = current_user.id
        data["establishment_id"] = space["establishment_id"]
        data["cost_credits"] = cost_credits
        data["status"] = ReservationStatus.CONFIRMED.value
        
        response = supabase.table("reservations").insert(data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create reservation"
            )
        
        return ReservationResponse(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create reservation: {str(e)}"
        )


@router.put("/{reservation_id}/cancel", response_model=ReservationResponse)
async def cancel_reservation(
    reservation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Cancel a reservation."""
    supabase = get_supabase()
    
    # Get reservation
    response = supabase.table("reservations").select("*").eq("id", reservation_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    reservation = response.data[0]
    
    # Verify ownership
    if reservation["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this reservation"
        )
    
    # Check if already cancelled or completed
    if reservation["status"] in [ReservationStatus.CANCELLED.value, ReservationStatus.COMPLETED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel this reservation"
        )
    
    # Update status to cancelled (trigger will handle refund)
    try:
        response = supabase.table("reservations").update({"status": ReservationStatus.CANCELLED.value}).eq("id", reservation_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel reservation"
            )
        
        return ReservationResponse(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel reservation: {str(e)}"
        )


@router.post("/{reservation_id}/check-in", response_model=ReservationResponse)
async def check_in_reservation(
    reservation_id: str,
    check_in_data: CheckInRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check in to a reservation using validation code."""
    supabase = get_supabase()
    
    # Get reservation
    response = supabase.table("reservations").select("*").eq("id", reservation_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    reservation = response.data[0]
    
    # Verify user owns this reservation or owns the establishment
    is_owner = False
    if reservation["user_id"] != current_user.id:
        # Check if user owns the establishment
        est_response = supabase.table("establishments").select("owner_id").eq("id", reservation["establishment_id"]).execute()
        if est_response.data and est_response.data[0]["owner_id"] == current_user.id:
            is_owner = True
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to check in this reservation"
            )
    
    # Verify validation code
    if reservation["validation_code"] != check_in_data.validation_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid validation code"
        )
    
    # Check reservation status
    if reservation["status"] != ReservationStatus.CONFIRMED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation is not in confirmed status"
        )
    
    # Check if within check-in window (e.g., 15 minutes before to 15 minutes after start time)
    now = datetime.now(reservation["start_time"].tzinfo)
    start_time = datetime.fromisoformat(reservation["start_time"])
    check_in_window_start = start_time - timedelta(minutes=15)
    check_in_window_end = start_time + timedelta(minutes=15)
    
    if not (check_in_window_start <= now <= check_in_window_end):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not within check-in window (15 minutes before to 15 minutes after start time)"
        )
    
    # Update reservation status
    try:
        response = supabase.table("reservations").update({
            "status": ReservationStatus.CHECKED_IN.value,
            "checked_in_at": now.isoformat()
        }).eq("id", reservation_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to check in"
            )
        
        return ReservationResponse(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to check in: {str(e)}"
        )


@router.get("/soonest/available")
async def find_soonest_available(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    limit: int = Query(10, ge=1, le=50)
):
    """Find soonest available spaces across all establishments."""
    supabase = get_supabase()
    
    # Get all active establishments and their spaces
    establishments_response = supabase.table("establishments").select("id, name, latitude, longitude, spaces(*)").eq("is_active", True).execute()
    
    if not establishments_response.data:
        return []
    
    # For each space, find next available slot
    available_slots = []
    now = datetime.now()
    
    for establishment in establishments_response.data:
        for space in establishment.get("spaces", []):
            if not space.get("is_available"):
                continue
            
            # Check if space is available in the next hour
            next_slot_start = now + timedelta(minutes=30)  # 30 minutes from now
            next_slot_end = next_slot_start + timedelta(hours=1)
            
            # Check for overlapping reservations
            reservations_response = supabase.table("reservations").select("start_time, end_time").eq("space_id", space["id"]).in_("status", [
                ReservationStatus.CONFIRMED.value,
                ReservationStatus.CHECKED_IN.value
            ]).gte("end_time", now.isoformat()).lte("start_time", (now + timedelta(days=1)).isoformat()).execute()
            
            # Find earliest available slot
            available_time = next_slot_start
            for reservation in reservations_response.data:
                res_start = datetime.fromisoformat(reservation["start_time"])
                res_end = datetime.fromisoformat(reservation["end_time"])
                
                if available_time < res_end and available_time + timedelta(hours=1) > res_start:
                    # Overlap, move to after this reservation
                    available_time = res_end
            
            available_slots.append({
                "establishment_id": establishment["id"],
                "establishment_name": establishment["name"],
                "space_id": space["id"],
                "space_name": space["name"],
                "available_at": available_time.isoformat(),
                "latitude": establishment["latitude"],
                "longitude": establishment["longitude"]
            })
    
    # Sort by available time
    available_slots.sort(key=lambda x: x["available_at"])
    
    # Calculate distance if coordinates provided
    if latitude is not None and longitude is not None:
        from geopy.distance import geodesic
        for slot in available_slots:
            distance = geodesic(
                (latitude, longitude),
                (slot["latitude"], slot["longitude"])
            ).kilometers
            slot["distance_km"] = round(distance, 2)
        
        # Sort by combination of time and distance
        available_slots.sort(key=lambda x: (x["available_at"], x.get("distance_km", 999)))
    
    return available_slots[:limit]

