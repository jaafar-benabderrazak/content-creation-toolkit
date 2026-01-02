from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.schemas import (
    UserResponse, UserProfileUpdate, UserProfileResponse, 
    UserReservationHistory, ReservationResponse
)
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user's profile with statistics."""
    supabase = get_supabase()
    
    # Get user profile
    user_response = supabase.table("users").select("*").eq("id", current_user.id).execute()
    
    if not user_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    user_data = user_response.data[0]
    
    # Get reservation count
    reservations = supabase.table("reservations").select("id", count="exact").eq("user_id", current_user.id).execute()
    total_reservations = reservations.count or 0
    
    # Get review count
    reviews = supabase.table("reviews").select("id", count="exact").eq("user_id", current_user.id).execute()
    total_reviews = reviews.count or 0
    
    return UserProfileResponse(
        **user_data,
        total_reservations=total_reservations,
        total_reviews=total_reviews
    )


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update current user's profile."""
    supabase = get_supabase()
    
    # Update profile
    update_data = profile_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to update"
        )
    
    try:
        response = supabase.table("users").update(update_data).eq("id", current_user.id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed"
            )
        
        user_data = response.data[0]
        
        # Get statistics
        reservations = supabase.table("reservations").select("id", count="exact").eq("user_id", current_user.id).execute()
        reviews = supabase.table("reviews").select("id", count="exact").eq("user_id", current_user.id).execute()
        
        return UserProfileResponse(
            **user_data,
            total_reservations=reservations.count or 0,
            total_reviews=reviews.count or 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update failed: {str(e)}"
        )


@router.get("/me/reservations", response_model=UserReservationHistory)
async def get_my_reservations(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None
):
    """Get current user's reservation history."""
    supabase = get_supabase()
    
    query = supabase.table("reservations").select("*").eq("user_id", current_user.id).order("created_at", desc=True)
    
    if status:
        query = query.eq("status", status)
    
    # Get total count
    count_response = query.execute()
    total_count = len(count_response.data)
    
    # Get paginated results
    query = query.range(offset, offset + limit - 1)
    response = query.execute()
    
    reservations = [ReservationResponse(**item) for item in response.data]
    
    # Calculate total spent
    total_spent = sum(r.cost_credits for r in reservations)
    
    return UserReservationHistory(
        reservations=reservations,
        total_count=total_count,
        total_spent_credits=total_spent
    )


@router.get("/me/stats")
async def get_my_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get current user's statistics."""
    supabase = get_supabase()
    
    # Get reservation stats
    reservations = supabase.table("reservations").select("*").eq("user_id", current_user.id).execute()
    
    total_reservations = len(reservations.data)
    completed_reservations = len([r for r in reservations.data if r["status"] == "completed"])
    cancelled_reservations = len([r for r in reservations.data if r["status"] == "cancelled"])
    active_reservations = len([r for r in reservations.data if r["status"] in ["pending", "confirmed", "checked_in"]])
    
    total_spent = sum(r["cost_credits"] for r in reservations.data)
    
    # Get review stats
    reviews = supabase.table("reviews").select("rating").eq("user_id", current_user.id).execute()
    total_reviews = len(reviews.data)
    average_rating_given = sum(r["rating"] for r in reviews.data) / total_reviews if total_reviews > 0 else None
    
    # Get favorite establishments (most visited)
    establishment_counts = {}
    for r in reservations.data:
        est_id = r["establishment_id"]
        establishment_counts[est_id] = establishment_counts.get(est_id, 0) + 1
    
    favorite_establishments = sorted(establishment_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Get establishment details
    favorite_establishments_details = []
    for est_id, count in favorite_establishments:
        est_response = supabase.table("establishments").select("id, name, category").eq("id", est_id).execute()
        if est_response.data:
            favorite_establishments_details.append({
                **est_response.data[0],
                "visit_count": count
            })
    
    return {
        "total_reservations": total_reservations,
        "completed_reservations": completed_reservations,
        "cancelled_reservations": cancelled_reservations,
        "active_reservations": active_reservations,
        "total_spent_credits": total_spent,
        "current_credits": current_user.coffee_credits,
        "total_reviews": total_reviews,
        "average_rating_given": average_rating_given,
        "favorite_establishments": favorite_establishments_details
    }


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    """Get public profile of a user (limited information)."""
    supabase = get_supabase()
    
    # Get user profile (only public fields)
    user_response = supabase.table("users").select("id, full_name, avatar_url, created_at").eq("id", user_id).execute()
    
    if not user_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_data = user_response.data[0]
    
    # Get review count
    reviews = supabase.table("reviews").select("id", count="exact").eq("user_id", user_id).execute()
    total_reviews = reviews.count or 0
    
    return {
        **user_data,
        "email": "hidden",  # Don't expose email
        "role": "customer",
        "coffee_credits": 0,  # Don't expose credits
        "updated_at": user_data["created_at"],
        "total_reservations": 0,  # Don't expose
        "total_reviews": total_reviews
    }

