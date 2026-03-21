"""
Email notification service for LibreWork using Resend.
Supports booking confirmation, cancellation, and marketing emails.
All functions degrade gracefully when RESEND_API_KEY is not configured.
"""
import logging
from typing import Optional

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_base_styles() -> str:
    return """
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #1a1a1a; color: white; padding: 24px 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 22px; }
        .accent { color: #F9AB18; }
        .content { background-color: #f9f9f9; padding: 24px; }
        .details { background-color: white; padding: 16px; border-left: 4px solid #F9AB18; margin: 16px 0; border-radius: 0 4px 4px 0; }
        .details p { margin: 6px 0; }
        .footer { text-align: center; color: #999; font-size: 12px; padding: 20px; background-color: #1a1a1a; border-radius: 0 0 8px 8px; }
        .footer p { margin: 4px 0; color: #ccc; }
    """


def send_booking_confirmation(
    to_email: str,
    user_name: str,
    space_name: str,
    start_time: str,
    end_time: str,
) -> Optional[dict]:
    """
    Send booking confirmation email via Resend.

    Returns the Resend response dict on success, or None if RESEND_API_KEY is
    not configured or if sending fails. Email failure never raises to the caller.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured — skipping booking confirmation email")
        return None

    try:
        resend.api_key = settings.RESEND_API_KEY

        html = f"""<!DOCTYPE html>
<html>
<head><style>{_get_base_styles()}</style></head>
<body>
  <div class="container">
    <div class="header">
      <h1>Libre<span class="accent">Work</span> — Booking Confirmed</h1>
    </div>
    <div class="content">
      <p>Hi {user_name},</p>
      <p>Your workspace reservation is confirmed. Here are the details:</p>
      <div class="details">
        <p><strong>Space:</strong> {space_name}</p>
        <p><strong>Start:</strong> {start_time}</p>
        <p><strong>End:</strong> {end_time}</p>
      </div>
      <p>We look forward to seeing you. If you need to cancel, please do so at least 2 hours in advance for a full refund.</p>
    </div>
    <div class="footer">
      <p>LibreWork &mdash; Find Your Perfect Workspace</p>
      <p>This is an automated message, please do not reply.</p>
    </div>
  </div>
</body>
</html>"""

        response = resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": "Booking Confirmed — LibreWork",
            "html": html,
        })
        return response
    except Exception as exc:
        logger.error("Failed to send booking confirmation email to %s: %s", to_email, exc)
        return None


def send_cancellation_email(
    to_email: str,
    user_name: str,
    space_name: str,
    start_time: str,
) -> Optional[dict]:
    """
    Send cancellation notification email via Resend.

    Returns the Resend response dict on success, or None if RESEND_API_KEY is
    not configured or if sending fails. Email failure never raises to the caller.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured — skipping cancellation email")
        return None

    try:
        resend.api_key = settings.RESEND_API_KEY

        html = f"""<!DOCTYPE html>
<html>
<head><style>{_get_base_styles()}</style></head>
<body>
  <div class="container">
    <div class="header">
      <h1>Libre<span class="accent">Work</span> — Reservation Cancelled</h1>
    </div>
    <div class="content">
      <p>Hi {user_name},</p>
      <p>Your reservation has been cancelled:</p>
      <div class="details">
        <p><strong>Space:</strong> {space_name}</p>
        <p><strong>Original Start:</strong> {start_time}</p>
      </div>
      <p>Any applicable credits have been refunded to your account per our cancellation policy.</p>
    </div>
    <div class="footer">
      <p>LibreWork &mdash; Find Your Perfect Workspace</p>
      <p>This is an automated message, please do not reply.</p>
    </div>
  </div>
</body>
</html>"""

        response = resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": "Reservation Cancelled — LibreWork",
            "html": html,
        })
        return response
    except Exception as exc:
        logger.error("Failed to send cancellation email to %s: %s", to_email, exc)
        return None


def send_marketing_email(
    to_emails: list[str],
    subject: str,
    html_content: str,
) -> Optional[dict]:
    """
    Send a marketing email to multiple recipients via Resend.

    Returns the Resend response dict on success, or None if RESEND_API_KEY is
    not configured or if sending fails.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured — skipping marketing email")
        return None

    if not to_emails:
        logger.warning("send_marketing_email called with empty recipient list")
        return None

    try:
        resend.api_key = settings.RESEND_API_KEY

        response = resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": to_emails,
            "subject": subject,
            "html": html_content,
        })
        return response
    except Exception as exc:
        logger.error("Failed to send marketing email: %s", exc)
        return None
