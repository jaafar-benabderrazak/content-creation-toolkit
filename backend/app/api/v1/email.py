"""
Email management endpoints for LibreWork.
Provides admin-only marketing email functionality.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.dependencies import get_current_admin
from app.core.email import send_marketing_email
from app.core.supabase import get_supabase
from app.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email"])


class MarketingEmailRequest(BaseModel):
    subject: str
    html_content: str


class MarketingEmailResponse(BaseModel):
    recipients_count: int
    message: str


@router.post(
    "/marketing/send",
    response_model=MarketingEmailResponse,
    status_code=status.HTTP_200_OK,
)
async def send_marketing_email_to_opted_in_users(
    payload: MarketingEmailRequest,
    current_admin: UserResponse = Depends(get_current_admin),
):
    """
    Send a marketing email to all users with marketing_opt_in=true.
    Admin only.

    If marketing_opt_in column does not exist in the users table, falls back to
    querying all users (v1 behaviour — add column migration later).
    """
    supabase = get_supabase()

    # Attempt to filter by marketing_opt_in; fall back to all users if column is absent
    try:
        users_response = (
            supabase.table("users")
            .select("email")
            .eq("marketing_opt_in", True)
            .execute()
        )
        recipient_emails: list[str] = [u["email"] for u in users_response.data if u.get("email")]
    except Exception as exc:
        logger.warning(
            "marketing_opt_in column query failed (%s) — falling back to all users", exc
        )
        try:
            users_response = supabase.table("users").select("email").execute()
            recipient_emails = [u["email"] for u in users_response.data if u.get("email")]
        except Exception as inner_exc:
            logger.error("Failed to fetch users for marketing email: %s", inner_exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch recipient list",
            )

    if not recipient_emails:
        return MarketingEmailResponse(
            recipients_count=0,
            message="No opted-in recipients found. Email not sent.",
        )

    result = send_marketing_email(
        to_emails=recipient_emails,
        subject=payload.subject,
        html_content=payload.html_content,
    )

    if result is None:
        # send_marketing_email logs internally; API still reports the count of intended recipients
        return MarketingEmailResponse(
            recipients_count=len(recipient_emails),
            message=(
                f"Email delivery skipped (RESEND_API_KEY not configured). "
                f"Would have sent to {len(recipient_emails)} recipient(s)."
            ),
        )

    return MarketingEmailResponse(
        recipients_count=len(recipient_emails),
        message=f"Marketing email sent to {len(recipient_emails)} recipient(s).",
    )
