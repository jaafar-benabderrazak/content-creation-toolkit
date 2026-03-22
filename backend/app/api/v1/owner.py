from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta, date
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


@router.get("/analytics/revenue")
async def get_revenue_analytics(
    period: str = Query("week", pattern="^(week|month|quarter)$"),
    current_user: UserResponse = Depends(get_current_owner)
) -> List[Dict[str, Any]]:
    """Get daily revenue time-series for the owner's establishments."""
    supabase = get_supabase()

    # Determine date range
    today = date.today()
    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    else:  # quarter
        days = 90
    start_date = today - timedelta(days=days - 1)

    # Get owner's establishments
    establishments = supabase.table("establishments").select("id").eq("owner_id", current_user.id).execute()
    establishment_ids = [e["id"] for e in establishments.data]

    if not establishment_ids:
        # Return zeroed series
        return [
            {"date": (start_date + timedelta(days=i)).isoformat(), "revenue": 0}
            for i in range(days)
        ]

    # Fetch all non-cancelled reservations in the period
    start_dt = datetime.combine(start_date, datetime.min.time()).isoformat()
    reservations = (
        supabase.table("reservations")
        .select("cost_credits,created_at")
        .in_("establishment_id", establishment_ids)
        .neq("status", "cancelled")
        .gte("created_at", start_dt)
        .execute()
    )

    # Group by date
    revenue_by_date: Dict[str, int] = {}
    for r in reservations.data:
        raw = r.get("created_at", "")
        try:
            res_date = datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
        except (ValueError, AttributeError):
            continue
        revenue_by_date[res_date] = revenue_by_date.get(res_date, 0) + (r.get("cost_credits") or 0)

    # Build complete series (fill missing days with 0)
    result = []
    for i in range(days):
        d = (start_date + timedelta(days=i)).isoformat()
        result.append({"date": d, "revenue": revenue_by_date.get(d, 0)})

    return result


@router.get("/analytics/occupancy")
async def get_occupancy_analytics(
    period: str = Query("week", pattern="^(week|month)$"),
    current_user: UserResponse = Depends(get_current_owner)
) -> List[Dict[str, Any]]:
    """Get daily occupancy time-series for the owner's establishments (simplified v1)."""
    supabase = get_supabase()

    days = 7 if period == "week" else 30
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    # Get owner's establishments
    establishments = supabase.table("establishments").select("id").eq("owner_id", current_user.id).execute()
    establishment_ids = [e["id"] for e in establishments.data]

    if not establishment_ids:
        return [
            {"date": (start_date + timedelta(days=i)).isoformat(), "occupancy": 0.0}
            for i in range(days)
        ]

    # Get total spaces count (denominator)
    spaces_response = supabase.table("spaces").select("id", count="exact").in_("establishment_id", establishment_ids).execute()
    total_spaces = spaces_response.count or 1  # avoid division by zero

    # Fetch confirmed reservations in the period
    start_dt = datetime.combine(start_date, datetime.min.time()).isoformat()
    reservations = (
        supabase.table("reservations")
        .select("created_at")
        .in_("establishment_id", establishment_ids)
        .eq("status", "confirmed")
        .gte("created_at", start_dt)
        .execute()
    )

    # Count by date
    count_by_date: Dict[str, int] = {}
    for r in reservations.data:
        raw = r.get("created_at", "")
        try:
            res_date = datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
        except (ValueError, AttributeError):
            continue
        count_by_date[res_date] = count_by_date.get(res_date, 0) + 1

    # Build complete series — occupancy = confirmed_reservations / total_spaces, capped at 1.0
    result = []
    for i in range(days):
        d = (start_date + timedelta(days=i)).isoformat()
        raw_occ = count_by_date.get(d, 0) / total_spaces
        result.append({"date": d, "occupancy": round(min(raw_occ, 1.0), 4)})

    return result


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

