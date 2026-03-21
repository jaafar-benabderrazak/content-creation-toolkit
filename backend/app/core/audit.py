"""
Audit Logging System for LibreWork
Based on CivilDocPro architecture - ISO/NF Compliance Ready
Tracks all critical operations: who did what, when, to which entity
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from app.core.supabase import get_supabase


# ============================================
# Audit Action Constants (for type safety)
# ============================================

class AuditAction(str, Enum):
    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REGISTER = "auth.register"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_PASSWORD_RESET = "auth.password_reset"
    AUTH_PASSWORD_RESET_REQUEST = "auth.password_reset_request"

    # Users
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ACTIVATE = "user.activate"
    USER_DEACTIVATE = "user.deactivate"
    USER_ROLE_ASSIGN = "user.role_assign"

    # Custom Roles
    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"

    # Establishments
    ESTABLISHMENT_CREATE = "establishment.create"
    ESTABLISHMENT_UPDATE = "establishment.update"
    ESTABLISHMENT_DELETE = "establishment.delete"
    ESTABLISHMENT_ARCHIVE = "establishment.archive"
    ESTABLISHMENT_RESTORE = "establishment.restore"

    # Spaces
    SPACE_CREATE = "space.create"
    SPACE_UPDATE = "space.update"
    SPACE_DELETE = "space.delete"

    # Reservations
    RESERVATION_CREATE = "reservation.create"
    RESERVATION_UPDATE = "reservation.update"
    RESERVATION_CANCEL = "reservation.cancel"
    RESERVATION_CHECK_IN = "reservation.check_in"
    RESERVATION_COMPLETE = "reservation.complete"

    # Credit Transactions
    CREDIT_PURCHASE = "credit.purchase"
    CREDIT_REFUND = "credit.refund"
    CREDIT_BONUS = "credit.bonus"

    # Reviews
    REVIEW_CREATE = "review.create"
    REVIEW_UPDATE = "review.update"
    REVIEW_DELETE = "review.delete"
    REVIEW_MODERATE = "review.moderate"

    # QR Codes
    QR_CODE_GENERATE = "qr.generate"
    QR_CODE_PRINT = "qr.print"

    # System/Admin
    SETTINGS_UPDATE = "settings.update"
    EXPORT_DATA = "export.data"


# Human-readable action descriptions
ACTION_DESCRIPTIONS: Dict[str, str] = {
    AuditAction.AUTH_LOGIN: "Connexion utilisateur",
    AuditAction.AUTH_LOGOUT: "Deconnexion utilisateur",
    AuditAction.AUTH_REGISTER: "Inscription utilisateur",
    AuditAction.AUTH_PASSWORD_CHANGE: "Changement de mot de passe",
    AuditAction.AUTH_PASSWORD_RESET: "Reinitialisation de mot de passe",
    AuditAction.AUTH_PASSWORD_RESET_REQUEST: "Demande de reinitialisation",
    AuditAction.USER_CREATE: "Creation utilisateur",
    AuditAction.USER_UPDATE: "Mise a jour utilisateur",
    AuditAction.USER_DELETE: "Suppression utilisateur",
    AuditAction.USER_ACTIVATE: "Activation utilisateur",
    AuditAction.USER_DEACTIVATE: "Desactivation utilisateur",
    AuditAction.USER_ROLE_ASSIGN: "Attribution de role",
    AuditAction.ROLE_CREATE: "Creation de role",
    AuditAction.ROLE_UPDATE: "Mise a jour de role",
    AuditAction.ROLE_DELETE: "Suppression de role",
    AuditAction.ESTABLISHMENT_CREATE: "Creation etablissement",
    AuditAction.ESTABLISHMENT_UPDATE: "Mise a jour etablissement",
    AuditAction.ESTABLISHMENT_DELETE: "Suppression etablissement",
    AuditAction.ESTABLISHMENT_ARCHIVE: "Archivage etablissement",
    AuditAction.ESTABLISHMENT_RESTORE: "Restauration etablissement",
    AuditAction.SPACE_CREATE: "Creation espace",
    AuditAction.SPACE_UPDATE: "Mise a jour espace",
    AuditAction.SPACE_DELETE: "Suppression espace",
    AuditAction.RESERVATION_CREATE: "Creation reservation",
    AuditAction.RESERVATION_UPDATE: "Mise a jour reservation",
    AuditAction.RESERVATION_CANCEL: "Annulation reservation",
    AuditAction.RESERVATION_CHECK_IN: "Check-in reservation",
    AuditAction.RESERVATION_COMPLETE: "Completion reservation",
    AuditAction.CREDIT_PURCHASE: "Achat credits",
    AuditAction.CREDIT_REFUND: "Remboursement credits",
    AuditAction.CREDIT_BONUS: "Bonus credits",
    AuditAction.REVIEW_CREATE: "Creation avis",
    AuditAction.REVIEW_UPDATE: "Mise a jour avis",
    AuditAction.REVIEW_DELETE: "Suppression avis",
    AuditAction.REVIEW_MODERATE: "Moderation avis",
    AuditAction.QR_CODE_GENERATE: "Generation QR code",
    AuditAction.QR_CODE_PRINT: "Impression QR code",
    AuditAction.SETTINGS_UPDATE: "Mise a jour parametres",
    AuditAction.EXPORT_DATA: "Export de donnees",
}


# ============================================
# Entity Types
# ============================================

class EntityType(str, Enum):
    USER = "user"
    ESTABLISHMENT = "establishment"
    SPACE = "space"
    RESERVATION = "reservation"
    CREDIT_TRANSACTION = "credit_transaction"
    REVIEW = "review"
    CUSTOM_ROLE = "custom_role"
    SYSTEM = "system"


# ============================================
# Audit Log Creation
# ============================================

async def create_audit_log(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    entity_label: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    previous_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an audit log entry.
    This is the main function to use when logging operations.
    """
    supabase = get_supabase()

    log_data = {
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_label": entity_label,
        "details": details or {},
        "previous_value": previous_value,
        "new_value": new_value,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }

    try:
        response = supabase.table("audit_logs").insert(log_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        # Log error but don't crash the application
        print(f"[Audit Log Error] Failed to create log: {e}")
        return None


# ============================================
# Convenience Functions for Common Operations
# ============================================

async def log_auth_action(
    user_id: str,
    action: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Log an authentication-related action."""
    return await create_audit_log(
        user_id=user_id,
        action=action,
        entity_type=EntityType.USER,
        entity_id=user_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_user_action(
    user_id: str,
    action: str,
    target_user_id: Optional[str] = None,
    target_user_email: Optional[str] = None,
    previous_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Log a user management action."""
    return await create_audit_log(
        user_id=user_id,
        action=action,
        entity_type=EntityType.USER,
        entity_id=target_user_id,
        entity_label=target_user_email,
        previous_value=previous_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_establishment_action(
    user_id: str,
    action: str,
    establishment_id: str,
    establishment_name: Optional[str] = None,
    previous_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Log an establishment-related action."""
    return await create_audit_log(
        user_id=user_id,
        action=action,
        entity_type=EntityType.ESTABLISHMENT,
        entity_id=establishment_id,
        entity_label=establishment_name,
        previous_value=previous_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_reservation_action(
    user_id: str,
    action: str,
    reservation_id: str,
    reservation_code: Optional[str] = None,
    previous_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Log a reservation-related action."""
    return await create_audit_log(
        user_id=user_id,
        action=action,
        entity_type=EntityType.RESERVATION,
        entity_id=reservation_id,
        entity_label=reservation_code,
        previous_value=previous_value,
        new_value=new_value,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_credit_action(
    user_id: str,
    action: str,
    transaction_id: Optional[str] = None,
    amount: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Log a credit transaction action."""
    return await create_audit_log(
        user_id=user_id,
        action=action,
        entity_type=EntityType.CREDIT_TRANSACTION,
        entity_id=transaction_id,
        entity_label=f"{amount} credits" if amount else None,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_review_action(
    user_id: str,
    action: str,
    review_id: str,
    establishment_name: Optional[str] = None,
    previous_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Log a review-related action."""
    return await create_audit_log(
        user_id=user_id,
        action=action,
        entity_type=EntityType.REVIEW,
        entity_id=review_id,
        entity_label=establishment_name,
        previous_value=previous_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ============================================
# Audit Log Queries
# ============================================

async def get_user_audit_logs(
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get audit logs for a specific user (actions performed by this user)."""
    supabase = get_supabase()

    response = (
        supabase.table("audit_logs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
        .execute()
    )

    return response.data or []


async def get_entity_audit_logs(
    entity_type: str,
    entity_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get audit logs for a specific entity."""
    supabase = get_supabase()

    response = (
        supabase.table("audit_logs")
        .select("*, users(email, full_name)")
        .eq("entity_type", entity_type)
        .eq("entity_id", entity_id)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
        .execute()
    )

    return response.data or []


async def get_recent_audit_logs(
    limit: int = 100,
    offset: int = 0,
    actions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Get recent audit logs (for admin dashboard)."""
    supabase = get_supabase()

    query = (
        supabase.table("audit_logs")
        .select("*, users(email, full_name)")
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )

    if actions:
        query = query.in_("action", actions)

    response = query.execute()
    return response.data or []


async def search_audit_logs(
    user_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Search audit logs with filters."""
    supabase = get_supabase()

    query = supabase.table("audit_logs").select("*, users(email, full_name)")

    if user_id:
        query = query.eq("user_id", user_id)
    if entity_type:
        query = query.eq("entity_type", entity_type)
    if action:
        query = query.eq("action", action)
    if start_date:
        query = query.gte("created_at", start_date.isoformat())
    if end_date:
        query = query.lte("created_at", end_date.isoformat())

    response = (
        query.order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
        .execute()
    )

    return response.data or []


# ============================================
# Audit Log Statistics
# ============================================

async def get_audit_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get audit log statistics for admin dashboard."""
    supabase = get_supabase()

    # Default to last 30 days if not specified
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        from datetime import timedelta
        start_date = end_date - timedelta(days=30)

    # Get counts by action type
    action_response = (
        supabase.table("audit_logs")
        .select("action, count")
        .gte("created_at", start_date.isoformat())
        .lte("created_at", end_date.isoformat())
        .execute()
    )

    # Get counts by entity type
    entity_response = (
        supabase.table("audit_logs")
        .select("entity_type, count")
        .gte("created_at", start_date.isoformat())
        .lte("created_at", end_date.isoformat())
        .execute()
    )

    # Get total count
    total_response = (
        supabase.table("audit_logs")
        .select("id", count="exact")
        .gte("created_at", start_date.isoformat())
        .lte("created_at", end_date.isoformat())
        .execute()
    )

    return {
        "total_logs": total_response.count if hasattr(total_response, 'count') else 0,
        "by_action": action_response.data or [],
        "by_entity": entity_response.data or [],
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
    }


# ============================================
# Helper Functions
# ============================================

def get_action_description(action: str) -> str:
    """Get human-readable description for an action."""
    return ACTION_DESCRIPTIONS.get(action, action)


def format_audit_log_for_display(log: Dict[str, Any]) -> Dict[str, Any]:
    """Format an audit log for UI display."""
    return {
        "id": log.get("id"),
        "action": log.get("action"),
        "action_description": get_action_description(log.get("action", "")),
        "entity_type": log.get("entity_type"),
        "entity_id": log.get("entity_id"),
        "entity_label": log.get("entity_label"),
        "user": log.get("users", {}),
        "timestamp": log.get("created_at"),
        "ip_address": log.get("ip_address"),
        "has_changes": log.get("previous_value") is not None or log.get("new_value") is not None,
        "details": log.get("details", {}),
    }
