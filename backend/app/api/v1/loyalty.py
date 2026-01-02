from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.schemas import UserResponse
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/loyalty", tags=["Loyalty & Rewards"])


# ============================================================================
# SCHEMAS
# ============================================================================

class LoyaltyStatus(BaseModel):
    user_id: str
    points: int
    tier_name: str
    tier_min_points: int
    tier_max_points: Optional[int]
    credits_bonus_percentage: int
    discount_percentage: int
    perks: List[str]
    lifetime_reservations: int
    lifetime_credits_spent: int
    current_streak_days: int
    longest_streak_days: int
    points_to_next_tier: Optional[int]
    next_tier_name: Optional[str]


class LoyaltyTransaction(BaseModel):
    id: str
    points: int
    transaction_type: str
    description: Optional[str]
    created_at: str


class RewardRedemption(BaseModel):
    reward_type: str  # free_credits, discount, perk
    points_cost: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/status", response_model=LoyaltyStatus)
async def get_loyalty_status(current_user: UserResponse = Depends(get_current_user)):
    """Get user's current loyalty status."""
    supabase = get_supabase()
    
    # Get loyalty data
    loyalty_response = supabase.table("user_loyalty")\
        .select("*, loyalty_tiers!inner(*)")\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not loyalty_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loyalty status not found"
        )
    
    loyalty = loyalty_response.data[0]
    tier = loyalty["loyalty_tiers"]
    
    # Get next tier
    next_tier_response = supabase.table("loyalty_tiers")\
        .select("*")\
        .gt("min_points", loyalty["points"])\
        .order("min_points")\
        .limit(1)\
        .execute()
    
    next_tier = next_tier_response.data[0] if next_tier_response.data else None
    points_to_next = next_tier["min_points"] - loyalty["points"] if next_tier else None
    
    return LoyaltyStatus(
        user_id=loyalty["user_id"],
        points=loyalty["points"],
        tier_name=tier["name"],
        tier_min_points=tier["min_points"],
        tier_max_points=tier.get("max_points"),
        credits_bonus_percentage=tier["credits_bonus_percentage"],
        discount_percentage=tier["discount_percentage"],
        perks=tier.get("perks", []),
        lifetime_reservations=loyalty["lifetime_reservations"],
        lifetime_credits_spent=loyalty["lifetime_credits_spent"],
        current_streak_days=loyalty["current_streak_days"],
        longest_streak_days=loyalty["longest_streak_days"],
        points_to_next_tier=points_to_next,
        next_tier_name=next_tier["name"] if next_tier else None
    )


@router.get("/transactions", response_model=List[LoyaltyTransaction])
async def get_loyalty_transactions(
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's loyalty transaction history."""
    supabase = get_supabase()
    
    response = supabase.table("loyalty_transactions")\
        .select("*")\
        .eq("user_id", current_user.id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return [LoyaltyTransaction(**transaction) for transaction in response.data]


@router.get("/tiers")
async def get_loyalty_tiers():
    """Get all available loyalty tiers."""
    supabase = get_supabase()
    
    response = supabase.table("loyalty_tiers")\
        .select("*")\
        .order("min_points")\
        .execute()
    
    return response.data


@router.post("/redeem/credits")
async def redeem_points_for_credits(
    points: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """Redeem loyalty points for coffee credits."""
    supabase = get_supabase()
    
    if points < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum 100 points required for redemption"
        )
    
    if points % 100 != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Points must be in multiples of 100"
        )
    
    # Check user has enough points
    loyalty_response = supabase.table("user_loyalty")\
        .select("points")\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not loyalty_response.data or loyalty_response.data[0]["points"] < points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient loyalty points"
        )
    
    # Calculate credits (100 points = 1 credit)
    credits_earned = points // 100
    
    # Deduct points
    supabase.table("user_loyalty")\
        .update({
            "points": loyalty_response.data[0]["points"] - points,
            "updated_at": datetime.utcnow().isoformat()
        })\
        .eq("user_id", current_user.id)\
        .execute()
    
    # Add credits
    supabase.table("users")\
        .update({
            "coffee_credits": current_user.coffee_credits + credits_earned
        })\
        .eq("id", current_user.id)\
        .execute()
    
    # Log loyalty transaction
    supabase.table("loyalty_transactions").insert({
        "user_id": current_user.id,
        "points": -points,
        "transaction_type": "redeemed",
        "description": f"Redeemed {points} points for {credits_earned} credits"
    }).execute()
    
    # Log credit transaction
    supabase.table("credit_transactions").insert({
        "user_id": current_user.id,
        "amount": credits_earned,
        "transaction_type": "purchase",
        "description": f"Earned from {points} loyalty points"
    }).execute()
    
    return {
        "message": "Points redeemed successfully",
        "points_redeemed": points,
        "credits_earned": credits_earned,
        "new_balance": current_user.coffee_credits + credits_earned
    }


@router.get("/leaderboard")
async def get_loyalty_leaderboard(limit: int = 100):
    """Get top users by loyalty points."""
    supabase = get_supabase()
    
    response = supabase.table("user_loyalty")\
        .select("*, users!inner(id, full_name)")\
        .order("points", desc=True)\
        .limit(limit)\
        .execute()
    
    leaderboard = []
    for i, entry in enumerate(response.data, 1):
        leaderboard.append({
            "rank": i,
            "user_id": entry["user_id"],
            "user_name": entry["users"]["full_name"],
            "points": entry["points"],
            "lifetime_reservations": entry["lifetime_reservations"]
        })
    
    return leaderboard


@router.post("/bonus/streak")
async def claim_streak_bonus(current_user: UserResponse = Depends(get_current_user)):
    """Claim bonus points for maintaining a streak."""
    supabase = get_supabase()
    
    loyalty_response = supabase.table("user_loyalty")\
        .select("current_streak_days, points, last_activity_date")\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not loyalty_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loyalty status not found"
        )
    
    loyalty = loyalty_response.data[0]
    streak_days = loyalty["current_streak_days"]
    
    if streak_days < 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum 7-day streak required. Current streak: {streak_days} days"
        )
    
    # Calculate bonus (50 points per week of streak)
    bonus_points = (streak_days // 7) * 50
    
    # Award bonus
    supabase.table("user_loyalty")\
        .update({
            "points": loyalty["points"] + bonus_points,
            "updated_at": datetime.utcnow().isoformat()
        })\
        .eq("user_id", current_user.id)\
        .execute()
    
    # Log transaction
    supabase.table("loyalty_transactions").insert({
        "user_id": current_user.id,
        "points": bonus_points,
        "transaction_type": "bonus",
        "description": f"Streak bonus: {streak_days} days"
    }).execute()
    
    return {
        "message": "Streak bonus claimed",
        "bonus_points": bonus_points,
        "streak_days": streak_days
    }

