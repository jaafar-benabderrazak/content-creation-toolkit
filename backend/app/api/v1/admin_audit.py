"""
Admin Audit Log API Endpoints
View and search audit logs for compliance and monitoring
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.core.auth_enhanced import get_current_admin
from app.core.audit import (
    get_recent_audit_logs, get_entity_audit_logs, search_audit_logs,
    get_audit_statistics, format_audit_log_for_display, get_action_description,
    AuditAction, EntityType
)

router = APIRouter(prefix="/admin/audit", tags=["Admin - Audit Logs"])


# ============================================
# Response Schemas
# ============================================

class AuditLogDetailResponse(BaseModel):
    id: str
    user_id: str
    user_email: Optional[str]
    user_full_name: Optional[str]
    action: str
    action_description: str
    entity_type: str
    entity_id: Optional[str]
    entity_label: Optional[str]
    details: Dict[str, Any]
    previous_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    has_changes: bool


class AuditStatisticsResponse(BaseModel):
    total_logs: int
    by_action: List[Dict[str, Any]]
    by_entity: List[Dict[str, Any]]
    date_range: Dict[str, str]


class AuditActionsListResponse(BaseModel):
    actions: List[Dict[str, str]]


# ============================================
# Audit Log Query Endpoints
# ============================================

@router.get("/logs", response_model=List[AuditLogDetailResponse])
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get audit logs with optional filtering.
    Admin only.
    """
    logs = await search_audit_logs(
        user_id=user_id,
        entity_type=entity_type,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

    # Format for display
    formatted_logs = []
    for log in logs:
        formatted = format_audit_log_for_display(log)

        # Add user details
        user = log.get("users", {})
        formatted["user_email"] = user.get("email")
        formatted["user_full_name"] = user.get("full_name")

        formatted_logs.append(AuditLogDetailResponse(**formatted))

    return formatted_logs


@router.get("/logs/entity/{entity_type}/{entity_id}", response_model=List[AuditLogDetailResponse])
async def get_entity_logs(
    entity_type: str,
    entity_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get audit logs for a specific entity.
    Admin only.
    """
    logs = await get_entity_audit_logs(entity_type, entity_id, limit, offset)

    formatted_logs = []
    for log in logs:
        formatted = format_audit_log_for_display(log)
        user = log.get("users", {})
        formatted["user_email"] = user.get("email")
        formatted["user_full_name"] = user.get("full_name")
        formatted_logs.append(AuditLogDetailResponse(**formatted))

    return formatted_logs


@router.get("/logs/recent", response_model=List[AuditLogDetailResponse])
async def get_recent_logs(
    limit: int = Query(100, ge=1, le=500),
    actions: Optional[List[str]] = Query(None),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get recent audit logs.
    Admin only.
    """
    logs = await get_recent_audit_logs(limit=limit, actions=actions)

    formatted_logs = []
    for log in logs:
        formatted = format_audit_log_for_display(log)
        user = log.get("users", {})
        formatted["user_email"] = user.get("email")
        formatted["user_full_name"] = user.get("full_name")
        formatted_logs.append(AuditLogDetailResponse(**formatted))

    return formatted_logs


@router.get("/logs/user/{user_id}", response_model=List[AuditLogDetailResponse])
async def get_user_logs(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get audit logs for a specific user (actions performed by this user).
    Admin only.
    """
    logs = await get_recent_audit_logs(limit=limit, offset=offset)

    # Filter by user_id
    user_logs = [log for log in logs if log.get("user_id") == user_id]

    formatted_logs = []
    for log in user_logs:
        formatted = format_audit_log_for_display(log)
        user = log.get("users", {})
        formatted["user_email"] = user.get("email")
        formatted["user_full_name"] = user.get("full_name")
        formatted_logs.append(AuditLogDetailResponse(**formatted))

    return formatted_logs


# ============================================
# Statistics Endpoints
# ============================================

@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get audit log statistics for a date range.
    Admin only.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    stats = await get_audit_statistics(start_date, end_date)

    return AuditStatisticsResponse(**stats)


@router.get("/statistics/dashboard")
async def get_audit_dashboard_stats(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get dashboard statistics for audit logs.
    Admin only.
    """
    # Last 24 hours
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)

    stats_24h = await get_audit_statistics(last_24h, now)
    stats_7d = await get_audit_statistics(last_7d, now)
    stats_30d = await get_audit_statistics(last_30d, now)

    return {
        "last_24h": {
            "total": stats_24h["total_logs"],
            "top_actions": stats_24h["by_action"][:5] if stats_24h["by_action"] else []
        },
        "last_7d": {
            "total": stats_7d["total_logs"],
            "top_actions": stats_7d["by_action"][:5] if stats_7d["by_action"] else []
        },
        "last_30d": {
            "total": stats_30d["total_logs"],
            "top_actions": stats_30d["by_action"][:5] if stats_30d["by_action"] else []
        }
    }


# ============================================
# Metadata Endpoints
# ============================================

@router.get("/actions", response_model=AuditActionsListResponse)
async def get_available_actions(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get list of all available audit actions with descriptions.
    Admin only.
    """
    actions = []
    for action in AuditAction:
        actions.append({
            "value": action.value,
            "description": get_action_description(action.value),
            "category": action.value.split(".")[0]
        })

    return AuditActionsListResponse(actions=actions)


@router.get("/entity-types")
async def get_entity_types(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get list of all entity types.
    Admin only.
    """
    return {
        "entity_types": [
            {"value": et.value, "label": et.value.replace("_", " ").title()}
            for et in EntityType
        ]
    }


# ============================================
# Export Endpoints
# ============================================

@router.get("/export")
async def export_audit_logs(
    start_date: datetime,
    end_date: datetime,
    format: str = Query("json", pattern=r"^(json|csv)$"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Export audit logs for a date range.
    Admin only.
    """
    logs = await search_audit_logs(
        start_date=start_date,
        end_date=end_date,
        limit=10000,  # Max export size
        offset=0
    )

    if format == "csv":
        # Generate CSV format
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID", "Timestamp", "User ID", "User Email", "Action",
            "Entity Type", "Entity ID", "Entity Label", "IP Address", "Details"
        ])

        # Data
        for log in logs:
            user = log.get("users", {})
            writer.writerow([
                log.get("id"),
                log.get("created_at"),
                log.get("user_id"),
                user.get("email", ""),
                log.get("action"),
                log.get("entity_type"),
                log.get("entity_id", ""),
                log.get("entity_label", ""),
                log.get("ip_address", ""),
                str(log.get("details", {}))
            ])

        return {
            "format": "csv",
            "data": output.getvalue(),
            "count": len(logs),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    # Default JSON format
    formatted_logs = []
    for log in logs:
        formatted = format_audit_log_for_display(log)
        user = log.get("users", {})
        formatted["user_email"] = user.get("email")
        formatted["user_full_name"] = user.get("full_name")
        formatted_logs.append(formatted)

    return {
        "format": "json",
        "logs": formatted_logs,
        "count": len(logs),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }
