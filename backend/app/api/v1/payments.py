from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from pydantic import BaseModel

import stripe

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.schemas import UserResponse

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/payments", tags=["Payments"])


class CheckoutSessionRequest(BaseModel):
    reservation_id: str


@router.post("/checkout-session")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a Stripe Checkout session for a pending reservation.

    Amount is always fetched from the DB — never from the request body.
    """
    supabase = get_supabase()

    # Fetch reservation joined with space name; never trust client-supplied amount
    response = (
        supabase.table("reservations")
        .select("id, user_id, status, cost_credits, space_id, spaces(name)")
        .eq("id", request.reservation_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    reservation = response.data[0]

    if reservation["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pay for this reservation",
        )

    if reservation["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reservation status is '{reservation['status']}', expected 'pending'",
        )

    cost_credits: int = reservation["cost_credits"]
    # 1 credit = 1 EUR cent
    amount_cents: int = cost_credits * 100

    space_name: str = reservation.get("spaces", {}).get("name", "Workspace") if reservation.get("spaces") else "Workspace"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=current_user.email,
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": space_name},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }
        ],
        success_url=f"{settings.FRONTEND_URL}/booking/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/booking/cancel",
        metadata={
            "reservation_id": request.reservation_id,
            "user_id": current_user.id,
        },
    )

    return {"checkout_url": session.url}


@router.patch("/reservations/{reservation_id}/confirm")
async def confirm_reservation(
    reservation_id: str,
    x_webhook_secret: Optional[str] = Header(None),
):
    """Internal endpoint called by the Next.js webhook handler after Stripe confirms payment.

    Validates the shared webhook secret so only the webhook handler can call this.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured",
        )

    if x_webhook_secret != settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    supabase = get_supabase()

    response = (
        supabase.table("reservations")
        .select("id, status")
        .eq("id", reservation_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    current_status = response.data[0]["status"]
    if current_status not in ("pending", "confirmed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm reservation with status '{current_status}'",
        )

    update_response = (
        supabase.table("reservations")
        .update({"status": "confirmed"})
        .eq("id", reservation_id)
        .execute()
    )

    if not update_response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to confirm reservation",
        )

    return {"status": "confirmed", "reservation_id": reservation_id}


@router.get("/history")
async def get_payment_history(
    current_user: UserResponse = Depends(get_current_user),
):
    """Return confirmed/completed reservations as payment history for current user.

    No separate payments table is needed for v1; reservation rows carry all relevant data.
    """
    supabase = get_supabase()

    response = (
        supabase.table("reservations")
        .select("id, space_id, cost_credits, status, created_at, start_time, end_time, spaces(name)")
        .eq("user_id", current_user.id)
        .in_("status", ["confirmed", "completed"])
        .order("created_at", desc=True)
        .execute()
    )

    records = []
    for row in response.data:
        space_name = row.get("spaces", {}).get("name", "Workspace") if row.get("spaces") else "Workspace"
        records.append(
            {
                "reservation_id": row["id"],
                "space_name": space_name,
                "amount_eur": row["cost_credits"] / 100,
                "status": row["status"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "created_at": row["created_at"],
            }
        )

    return records
