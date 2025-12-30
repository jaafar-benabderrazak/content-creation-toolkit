from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas import (
    CreditBalance, CreditPurchase, CreditTransactionResponse,
    UserResponse, TransactionType
)
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/credits", tags=["Credits"])


@router.get("/balance", response_model=CreditBalance)
async def get_credit_balance(current_user: UserResponse = Depends(get_current_user)):
    """Get current user's credit balance."""
    return CreditBalance(
        balance=current_user.coffee_credits,
        user_id=current_user.id
    )


@router.get("/transactions", response_model=List[CreditTransactionResponse])
async def get_credit_transactions(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 50
):
    """Get user's credit transaction history."""
    supabase = get_supabase()
    
    response = supabase.table("credit_transactions").select("*").eq("user_id", current_user.id).order("created_at", desc=True).limit(limit).execute()
    
    return [CreditTransactionResponse(**item) for item in response.data]


@router.post("/purchase", response_model=CreditBalance)
async def purchase_credits(
    purchase_data: CreditPurchase,
    current_user: UserResponse = Depends(get_current_user)
):
    """Purchase credits (symbolic payment for demo)."""
    supabase = get_supabase()
    
    # In a real application, integrate with Stripe/PayPal here
    # For now, just add credits (symbolic)
    
    try:
        # Update user credits
        new_balance = current_user.coffee_credits + purchase_data.amount
        update_response = supabase.table("users").update({
            "coffee_credits": new_balance
        }).eq("id", current_user.id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update credits"
            )
        
        # Record transaction
        transaction_data = {
            "user_id": current_user.id,
            "amount": purchase_data.amount,
            "transaction_type": TransactionType.PURCHASE.value,
            "description": f"Purchased {purchase_data.amount} coffee credits"
        }
        
        supabase.table("credit_transactions").insert(transaction_data).execute()
        
        return CreditBalance(
            balance=new_balance,
            user_id=current_user.id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to purchase credits: {str(e)}"
        )


@router.post("/bonus/{user_id}", response_model=CreditBalance)
async def grant_bonus_credits(
    user_id: str,
    amount: int,
    description: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Grant bonus credits to a user (admin only - demo endpoint)."""
    supabase = get_supabase()
    
    # In production, add admin check
    # For demo purposes, allowing any authenticated user
    
    try:
        # Get target user
        user_response = supabase.table("users").select("coffee_credits").eq("id", user_id).execute()
        
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        current_balance = user_response.data[0]["coffee_credits"]
        new_balance = current_balance + amount
        
        # Update credits
        update_response = supabase.table("users").update({
            "coffee_credits": new_balance
        }).eq("id", user_id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to grant credits"
            )
        
        # Record transaction
        transaction_data = {
            "user_id": user_id,
            "amount": amount,
            "transaction_type": TransactionType.BONUS.value,
            "description": description
        }
        
        supabase.table("credit_transactions").insert(transaction_data).execute()
        
        return CreditBalance(
            balance=new_balance,
            user_id=user_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to grant credits: {str(e)}"
        )

