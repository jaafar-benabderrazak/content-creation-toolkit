from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from app.schemas import ReviewCreate, ReviewUpdate, ReviewResponse, UserResponse
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/establishment/{establishment_id}", response_model=List[ReviewResponse])
async def get_establishment_reviews(
    establishment_id: str,
    limit: int = Query(50, ge=1, le=100)
):
    """Get reviews for an establishment."""
    supabase = get_supabase()
    
    response = supabase.table("reviews").select("*").eq("establishment_id", establishment_id).order("created_at", desc=True).limit(limit).execute()
    
    return [ReviewResponse(**item) for item in response.data]


@router.get("/user/{user_id}", response_model=List[ReviewResponse])
async def get_user_reviews(
    user_id: str,
    limit: int = Query(50, ge=1, le=100)
):
    """Get reviews by a user."""
    supabase = get_supabase()
    
    response = supabase.table("reviews").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    
    return [ReviewResponse(**item) for item in response.data]


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a review for a completed reservation."""
    supabase = get_supabase()
    
    # Verify reservation exists and is completed
    reservation_response = supabase.table("reservations").select("*").eq("id", review_data.reservation_id).execute()
    
    if not reservation_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    reservation = reservation_response.data[0]
    
    # Verify user owns the reservation
    if reservation["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this reservation"
        )
    
    # Verify reservation is completed
    if reservation["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review completed reservations"
        )
    
    # Check if review already exists
    existing_review = supabase.table("reviews").select("id").eq("reservation_id", review_data.reservation_id).eq("user_id", current_user.id).execute()
    
    if existing_review.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this reservation"
        )
    
    # Create review
    try:
        data = review_data.model_dump()
        data["user_id"] = current_user.id
        
        response = supabase.table("reviews").insert(data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create review"
            )
        
        return ReviewResponse(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create review: {str(e)}"
        )


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    review_update: ReviewUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a review."""
    supabase = get_supabase()
    
    # Get review
    response = supabase.table("reviews").select("*").eq("id", review_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    review = response.data[0]
    
    # Verify ownership
    if review["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review"
        )
    
    # Update review
    update_data = review_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to update"
        )
    
    try:
        response = supabase.table("reviews").update(update_data).eq("id", review_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed"
            )
        
        return ReviewResponse(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a review."""
    supabase = get_supabase()
    
    # Get review
    response = supabase.table("reviews").select("user_id").eq("id", review_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Verify ownership
    if response.data[0]["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review"
        )
    
    # Delete review
    try:
        supabase.table("reviews").delete().eq("id", review_id).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delete failed: {str(e)}"
        )

