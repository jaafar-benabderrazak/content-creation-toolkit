from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas import (
    UserResponse, OwnerDashboardStats, EstablishmentStats, EstablishmentResponse
)
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_owner

router = APIRouter(prefix="/owner", tags=["Owner Dashboard"])


@router.get("/dashboard", response_model=OwnerDashboardStats)
async def get_owner_dashboard(current_user: UserResponse = Depends(get_current_owner)):
    """Get owner dashboard statistics."""
    supabase = get_supabase()
    
    # Get owner's establishments
    establishments = supabase.table("establishments").select("id").eq("owner_id", current_user.id).execute()
    establishment_ids = [e["id"] for e in establishments.data]
    
    if not establishment_ids:
        return OwnerDashboardStats(
            total_establishments=0,
            total_spaces=0,
            total_reservations=0,
            total_revenue_credits=0,
            active_reservations=0,
            pending_reservations=0,
            average_rating=None,
            total_reviews=0
        )
    
    # Get total spaces
    spaces_response = supabase.table("spaces").select("id", count="exact").in_("establishment_id", establishment_ids).execute()
    total_spaces = spaces_response.count or 0
    
    # Get reservations
    reservations = supabase.table("reservations").select("*").in_("establishment_id", establishment_ids).execute()
    
    total_reservations = len(reservations.data)
    active_reservations = len([r for r in reservations.data if r["status"] in ["confirmed", "checked_in"]])
    pending_reservations = len([r for r in reservations.data if r["status"] == "pending"])
    
    total_revenue = sum(r["cost_credits"] for r in reservations.data if r["status"] != "cancelled")
    
    # Get reviews
    reviews = supabase.table("reviews").select("rating").in_("establishment_id", establishment_ids).execute()
    total_reviews = len(reviews.data)
    average_rating = sum(r["rating"] for r in reviews.data) / total_reviews if total_reviews > 0 else None
    
    return OwnerDashboardStats(
        total_establishments=len(establishment_ids),
        total_spaces=total_spaces,
        total_reservations=total_reservations,
        total_revenue_credits=total_revenue,
        active_reservations=active_reservations,
        pending_reservations=pending_reservations,
        average_rating=average_rating,
        total_reviews=total_reviews
    )


@router.get("/establishments", response_model=List[EstablishmentResponse])
async def get_owner_establishments(current_user: UserResponse = Depends(get_current_owner)):
    """Get all establishments owned by the current user."""
    supabase = get_supabase()
    
    response = supabase.table("establishments").select("*").eq("owner_id", current_user.id).order("created_at", desc=True).execute()
    
    return [EstablishmentResponse(**item) for item in response.data]


@router.get("/establishments/{establishment_id}/stats", response_model=EstablishmentStats)
async def get_establishment_stats(
    establishment_id: str,
    current_user: UserResponse = Depends(get_current_owner)
):
    """Get statistics for a specific establishment."""
    supabase = get_supabase()
    
    # Verify ownership
    est_response = supabase.table("establishments").select("*").eq("id", establishment_id).eq("owner_id", current_user.id).execute()
    
    if not est_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found or not owned by you"
        )
    
    establishment = est_response.data[0]
    
    # Get spaces count
    spaces = supabase.table("spaces").select("id", count="exact").eq("establishment_id", establishment_id).execute()
    total_spaces = spaces.count or 0
    
    # Get reservations
    reservations = supabase.table("reservations").select("*").eq("establishment_id", establishment_id).execute()
    
    total_reservations = len(reservations.data)
    active_reservations = len([r for r in reservations.data if r["status"] in ["confirmed", "checked_in"]])
    
    revenue_credits = sum(r["cost_credits"] for r in reservations.data if r["status"] != "cancelled")
    
    # Get reviews
    reviews = supabase.table("reviews").select("rating").eq("establishment_id", establishment_id).execute()
    total_reviews = len(reviews.data)
    average_rating = sum(r["rating"] for r in reviews.data) / total_reviews if total_reviews > 0 else None
    
    # Calculate occupancy rate (simplified)
    completed_reservations = len([r for r in reservations.data if r["status"] == "completed"])
    occupancy_rate = (completed_reservations / (total_spaces * 30)) * 100 if total_spaces > 0 else 0.0  # Rough estimate per month
    occupancy_rate = min(occupancy_rate, 100.0)
    
    return EstablishmentStats(
        establishment_id=establishment_id,
        establishment_name=establishment["name"],
        total_spaces=total_spaces,
        total_reservations=total_reservations,
        revenue_credits=revenue_credits,
        active_reservations=active_reservations,
        average_rating=average_rating,
        total_reviews=total_reviews,
        occupancy_rate=round(occupancy_rate, 2)
    )


@router.get("/reservations")
async def get_owner_reservations(
    current_user: UserResponse = Depends(get_current_owner),
    status: str = None
):
    """Get all reservations for owner's establishments."""
    supabase = get_supabase()
    
    # Get owner's establishments
    establishments = supabase.table("establishments").select("id").eq("owner_id", current_user.id).execute()
    establishment_ids = [e["id"] for e in establishments.data]
    
    if not establishment_ids:
        return []
    
    # Get reservations
    query = supabase.table("reservations").select("*, spaces!inner(name, establishment_id), users!inner(full_name, email)").in_("establishment_id", establishment_ids).order("created_at", desc=True)
    
    if status:
        query = query.eq("status", status)
    
    response = query.execute()
    
    return response.data

