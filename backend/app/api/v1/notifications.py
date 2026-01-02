from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.schemas import UserResponse
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user
import json

router = APIRouter(prefix="/notifications", tags=["Push Notifications"])


# ============================================================================
# SCHEMAS
# ============================================================================

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict  # Contains p256dh and auth


class NotificationCreate(BaseModel):
    title: str
    body: str
    data: Optional[dict] = {}


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/subscribe")
async def subscribe_to_push(
    subscription: PushSubscription,
    device_name: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Subscribe to push notifications."""
    supabase = get_supabase()
    
    try:
        result = supabase.table("push_subscriptions").insert({
            "user_id": current_user.id,
            "endpoint": subscription.endpoint,
            "p256dh": subscription.keys.get("p256dh"),
            "auth": subscription.keys.get("auth"),
            "device_name": device_name,
            "created_at": datetime.utcnow().isoformat(),
            "last_used_at": datetime.utcnow().isoformat()
        }).execute()
        
        return {"message": "Subscribed to push notifications", "id": result.data[0]["id"]}
    except Exception as e:
        # Handle duplicate subscription
        if "duplicate key value" in str(e).lower():
            # Update last_used_at
            supabase.table("push_subscriptions")\
                .update({"last_used_at": datetime.utcnow().isoformat()})\
                .eq("user_id", current_user.id)\
                .eq("endpoint", subscription.endpoint)\
                .execute()
            return {"message": "Subscription updated"}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/unsubscribe")
async def unsubscribe_from_push(
    endpoint: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Unsubscribe from push notifications."""
    supabase = get_supabase()
    
    supabase.table("push_subscriptions")\
        .delete()\
        .eq("user_id", current_user.id)\
        .eq("endpoint", endpoint)\
        .execute()
    
    return {"message": "Unsubscribed from push notifications"}


@router.get("/subscriptions")
async def get_subscriptions(current_user: UserResponse = Depends(get_current_user)):
    """Get user's push subscriptions."""
    supabase = get_supabase()
    
    response = supabase.table("push_subscriptions")\
        .select("id, endpoint, device_name, created_at, last_used_at")\
        .eq("user_id", current_user.id)\
        .execute()
    
    return response.data


@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get notification history."""
    supabase = get_supabase()
    
    response = supabase.table("notification_queue")\
        .select("*")\
        .eq("user_id", current_user.id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return response.data


@router.get("/preferences")
async def get_notification_preferences(current_user: UserResponse = Depends(get_current_user)):
    """Get user's notification preferences."""
    supabase = get_supabase()
    
    response = supabase.table("notification_preferences")\
        .select("*")\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not response.data:
        # Create default preferences
        default_prefs = supabase.table("notification_preferences").insert({
            "user_id": current_user.id,
            "email_reservations": True,
            "email_cancellations": True,
            "email_reminders": True,
            "email_promotions": False,
            "push_reservations": True,
            "push_reminders": True,
            "reminder_hours_before": 2
        }).execute()
        return default_prefs.data[0]
    
    return response.data[0]


@router.put("/preferences")
async def update_notification_preferences(
    preferences: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user's notification preferences."""
    supabase = get_supabase()
    
    preferences["updated_at"] = datetime.utcnow().isoformat()
    
    result = supabase.table("notification_preferences")\
        .update(preferences)\
        .eq("user_id", current_user.id)\
        .execute()
    
    return {"message": "Preferences updated", "preferences": result.data[0]}


@router.post("/test")
async def send_test_notification(current_user: UserResponse = Depends(get_current_user)):
    """Send a test push notification."""
    supabase = get_supabase()
    
    # Queue a test notification
    supabase.table("notification_queue").insert({
        "user_id": current_user.id,
        "title": "Test Notification",
        "body": "This is a test notification from LibreWork!",
        "data": json.dumps({"type": "test"}),
        "status": "pending"
    }).execute()
    
    return {"message": "Test notification queued. You should receive it shortly."}


# ============================================================================
# HELPER FUNCTIONS (for backend to queue notifications)
# ============================================================================

async def queue_notification(user_id: str, title: str, body: str, data: dict = None):
    """Queue a notification to be sent (used by other parts of the app)."""
    supabase = get_supabase()
    
    supabase.table("notification_queue").insert({
        "user_id": user_id,
        "title": title,
        "body": body,
        "data": json.dumps(data or {}),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }).execute()

