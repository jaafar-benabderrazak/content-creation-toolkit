from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from app.schemas import UserResponse, EstablishmentResponse
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/{establishment_id}")
async def add_favorite(
    establishment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Add establishment to user's favorites."""
    supabase = get_supabase()
    
    # Check if establishment exists
    est_response = supabase.table("establishments").select("id").eq("id", establishment_id).execute()
    if not est_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )
    
    try:
        response = supabase.table("user_favorites").insert({
            "user_id": current_user.id,
            "establishment_id": establishment_id,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        return {"message": "Added to favorites", "id": response.data[0]["id"]}
    except Exception as e:
        # Handle duplicate favorite
        if "duplicate key value" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already in favorites"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{establishment_id}")
async def remove_favorite(
    establishment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Remove establishment from favorites."""
    supabase = get_supabase()
    
    supabase.table("user_favorites")\
        .delete()\
        .eq("user_id", current_user.id)\
        .eq("establishment_id", establishment_id)\
        .execute()
    
    return {"message": "Removed from favorites"}


@router.get("", response_model=List[EstablishmentResponse])
async def get_favorites(current_user: UserResponse = Depends(get_current_user)):
    """Get user's favorite establishments."""
    supabase = get_supabase()
    
    # Get favorites with establishment details
    response = supabase.table("user_favorites")\
        .select("establishment_id, establishments!inner(*)")\
        .eq("user_id", current_user.id)\
        .order("created_at", desc=True)\
        .execute()
    
    # Extract establishment data
    establishments = []
    for item in response.data:
        if "establishments" in item and item["establishments"]:
            establishments.append(EstablishmentResponse(**item["establishments"]))
    
    return establishments


@router.get("/check/{establishment_id}")
async def check_favorite(
    establishment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if an establishment is in user's favorites."""
    supabase = get_supabase()
    
    response = supabase.table("user_favorites")\
        .select("id")\
        .eq("user_id", current_user.id)\
        .eq("establishment_id", establishment_id)\
        .execute()
    
    return {"is_favorite": len(response.data) > 0}

