from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.schemas import UserResponse
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/heatmap")
async def get_activity_heatmap(current_user: UserResponse = Depends(get_current_user)):
    """Get user's activity heatmap (7 days x 24 hours)."""
    supabase = get_supabase()
    
    # Get user's reservations from last 90 days
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    
    response = supabase.table("reservations")\
        .select("start_time, end_time, status")\
        .eq("user_id", current_user.id)\
        .in_("status", ["confirmed", "completed"])\
        .gte("start_time", ninety_days_ago.isoformat())\
        .execute()
    
    # Initialize 7x24 matrix
    heatmap = [[0 for _ in range(24)] for _ in range(7)]
    
    # Process each reservation
    for reservation in response.data:
        start = datetime.fromisoformat(reservation["start_time"])
        end = datetime.fromisoformat(reservation["end_time"])
        
        # Count each hour in the reservation
        current = start
        while current < end:
            day_of_week = current.weekday()  # 0=Monday, 6=Sunday
            hour = current.hour
            heatmap[day_of_week][hour] += 1
            current += timedelta(hours=1)
    
    return {
        "heatmap": heatmap,
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "total_hours": sum(sum(row) for row in heatmap)
    }


@router.get("/history")
async def get_activity_history(
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's activity history."""
    supabase = get_supabase()
    
    response = supabase.table("user_activity_log")\
        .select("*, establishments(name), reservations(start_time, end_time)")\
        .eq("user_id", current_user.id)\
        .order("activity_timestamp", desc=True)\
        .limit(limit)\
        .execute()
    
    return {
        "activities": response.data,
        "count": len(response.data)
    }


@router.get("/stats")
async def get_activity_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get user's activity statistics."""
    supabase = get_supabase()
    
    # Get all reservations
    reservations_response = supabase.table("reservations")\
        .select("*")\
        .eq("user_id", current_user.id)\
        .execute()
    
    total_reservations = len(reservations_response.data)
    completed_reservations = len([r for r in reservations_response.data if r["status"] == "completed"])
    cancelled_reservations = len([r for r in reservations_response.data if r["status"] == "cancelled"])
    
    # Calculate total hours and credits
    total_hours = 0
    total_credits_spent = 0
    
    for reservation in reservations_response.data:
        if reservation["status"] in ["confirmed", "completed"]:
            start = datetime.fromisoformat(reservation["start_time"])
            end = datetime.fromisoformat(reservation["end_time"])
            hours = (end - start).total_seconds() / 3600
            total_hours += hours
            total_credits_spent += reservation.get("total_credits", 0)
    
    # Get favorite establishments
    favorites_response = supabase.table("user_favorites")\
        .select("id", count="exact")\
        .eq("user_id", current_user.id)\
        .execute()
    
    # Get review count
    reviews_response = supabase.table("reviews")\
        .select("id", count="exact")\
        .eq("user_id", current_user.id)\
        .execute()
    
    # Get most visited establishments
    establishment_visits = {}
    for reservation in reservations_response.data:
        if reservation["status"] in ["confirmed", "completed"]:
            est_id = reservation["establishment_id"]
            establishment_visits[est_id] = establishment_visits.get(est_id, 0) + 1
    
    most_visited = []
    if establishment_visits:
        top_3_ids = sorted(establishment_visits.items(), key=lambda x: x[1], reverse=True)[:3]
        for est_id, count in top_3_ids:
            est_response = supabase.table("establishments")\
                .select("id, name, category")\
                .eq("id", est_id)\
                .execute()
            if est_response.data:
                most_visited.append({
                    **est_response.data[0],
                    "visit_count": count
                })
    
    return {
        "total_reservations": total_reservations,
        "completed_reservations": completed_reservations,
        "cancelled_reservations": cancelled_reservations,
        "total_hours": round(total_hours, 1),
        "total_credits_spent": total_credits_spent,
        "favorite_count": favorites_response.count or 0,
        "review_count": reviews_response.count or 0,
        "most_visited_establishments": most_visited
    }


@router.get("/streaks")
async def get_activity_streaks(current_user: UserResponse = Depends(get_current_user)):
    """Get user's activity streaks."""
    supabase = get_supabase()
    
    # Get all completed reservations ordered by date
    response = supabase.table("reservations")\
        .select("start_time")\
        .eq("user_id", current_user.id)\
        .eq("status", "completed")\
        .order("start_time")\
        .execute()
    
    if not response.data:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity": None
        }
    
    # Extract unique dates
    dates = set()
    for reservation in response.data:
        date = datetime.fromisoformat(reservation["start_time"]).date()
        dates.add(date)
    
    sorted_dates = sorted(dates)
    
    # Calculate current streak
    current_streak = 0
    today = datetime.utcnow().date()
    
    if sorted_dates[-1] >= today - timedelta(days=1):
        current_streak = 1
        for i in range(len(sorted_dates) - 2, -1, -1):
            if (sorted_dates[i+1] - sorted_dates[i]).days == 1:
                current_streak += 1
            else:
                break
    
    # Calculate longest streak
    longest_streak = 1
    temp_streak = 1
    
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "last_activity": sorted_dates[-1].isoformat() if sorted_dates else None,
        "total_active_days": len(dates)
    }

