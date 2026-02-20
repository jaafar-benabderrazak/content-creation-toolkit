"""
Role-Based Access Control (RBAC) for LibreWork.
3 fixed roles: customer, owner, admin. No custom roles table.
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from fastapi import Depends, HTTPException, Request, status

from app.core.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.schemas import UserResponse


class PermissionModule(str, Enum):
    DASHBOARD = "dashboard"
    ESTABLISHMENTS = "establishments"
    SPACES = "spaces"
    RESERVATIONS = "reservations"
    USERS = "users"
    BILLING = "billing"
    REVIEWS = "reviews"
    ADMIN = "admin"


class PermissionAction(str, Enum):
    VIEW = "view"
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    ARCHIVE = "archive"
    EXPORT = "export"
    VALIDATE = "validate"
    ASSIGN = "assign"
    MANAGE = "manage"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SETTINGS = "manage_settings"


MODULE_LABELS: Dict[str, str] = {
    "dashboard": "Tableau de bord",
    "establishments": "Etablissements",
    "spaces": "Espaces",
    "reservations": "Reservations",
    "users": "Utilisateurs",
    "billing": "Facturation",
    "reviews": "Avis",
    "admin": "Administration",
}

ACTION_LABELS: Dict[str, str] = {
    "view": "Voir",
    "create": "Creer",
    "edit": "Modifier",
    "delete": "Supprimer",
    "archive": "Archiver",
    "export": "Exporter",
    "validate": "Valider",
    "assign": "Assigner",
    "manage": "Gerer",
    "manage_users": "Gerer les utilisateurs",
    "manage_roles": "Gerer les roles",
    "manage_settings": "Gerer les parametres",
}

MODULE_ACTIONS: Dict[str, List[str]] = {
    "dashboard": ["view"],
    "establishments": ["view", "create", "edit", "archive", "delete"],
    "spaces": ["view", "create", "edit", "delete"],
    "reservations": ["view", "create", "edit", "cancel", "validate"],
    "users": ["view", "create", "edit", "deactivate", "manage_roles"],
    "billing": ["view", "manage", "export"],
    "reviews": ["view", "moderate", "delete"],
    "admin": ["view", "manage_users", "manage_roles", "manage_settings"],
}


DEFAULT_ROLE_PERMISSIONS: Dict[str, Dict[str, Dict[str, bool]]] = {
    "admin": {
        "dashboard": {"view": True},
        "establishments": {"view": True, "create": True, "edit": True, "archive": True, "delete": True},
        "spaces": {"view": True, "create": True, "edit": True, "delete": True},
        "reservations": {"view": True, "create": True, "edit": True, "cancel": True, "validate": True},
        "users": {"view": True, "create": True, "edit": True, "deactivate": True, "manage_roles": True},
        "billing": {"view": True, "manage": True, "export": True},
        "reviews": {"view": True, "moderate": True, "delete": True},
        "admin": {"view": True, "manage_users": True, "manage_roles": True, "manage_settings": True},
    },
    "owner": {
        "dashboard": {"view": True},
        "establishments": {"view": True, "create": True, "edit": True, "archive": True, "delete": True},
        "spaces": {"view": True, "create": True, "edit": True, "delete": True},
        "reservations": {"view": True, "create": False, "edit": True, "cancel": True, "validate": True},
        "users": {"view": True, "create": False, "edit": False, "deactivate": False, "manage_roles": False},
        "billing": {"view": True, "manage": True, "export": True},
        "reviews": {"view": True, "moderate": True, "delete": False},
        "admin": {},
    },
    "customer": {
        "dashboard": {"view": True},
        "establishments": {"view": True, "create": False, "edit": False, "archive": False, "delete": False},
        "spaces": {"view": True, "create": False, "edit": False, "delete": False},
        "reservations": {"view": True, "create": True, "edit": True, "cancel": True, "validate": False},
        "users": {},
        "billing": {"view": True, "manage": False, "export": False},
        "reviews": {"view": True, "moderate": False, "delete": False},
        "admin": {},
    },
}


# ---- Permission Resolution (fixed roles only) ----

def resolve_user_permissions(role: str) -> Dict[str, Dict[str, bool]]:
    """Resolve effective permissions for a role. Admin always gets full permissions."""
    if role == "admin":
        return DEFAULT_ROLE_PERMISSIONS["admin"]
    return DEFAULT_ROLE_PERMISSIONS.get(role, {})


def has_permission(role: str, module: str, action: str) -> bool:
    """Check if a role has a specific permission on a module."""
    permissions = resolve_user_permissions(role)
    module_perms = permissions.get(module, {})
    return module_perms.get(action, False)


def has_any_permission(role: str, module: str, actions: List[str]) -> bool:
    """Check if a role has any of the specified permissions on a module."""
    permissions = resolve_user_permissions(role)
    module_perms = permissions.get(module, {})
    return any(module_perms.get(action, False) for action in actions)


# ---- FastAPI Dependencies ----

def require_permission(module: str, action: str):
    """Dependency factory: require a specific module + action permission."""
    async def checker(request: Request):
        user = await get_current_user(request)
        if user.role == "admin":
            return user
        if not has_permission(user.role, module, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {module}.{action}",
            )
        return user
    return checker


def require_any_permission(module: str, actions: List[str]):
    """Dependency factory: require any of the specified permissions."""
    async def checker(request: Request):
        user = await get_current_user(request)
        if user.role == "admin":
            return user
        if not has_any_permission(user.role, module, actions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires any of {actions} on {module}",
            )
        return user
    return checker


def require_role(*roles: str):
    """Dependency factory: require one of the given roles."""
    async def checker(request: Request):
        user = await get_current_user(request)
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(roles)}",
            )
        return user
    return checker


# ---- Establishment Access Control ----

async def check_establishment_access(
    user_id: str,
    establishment_id: str,
    user_role: str,
) -> Dict[str, Any]:
    """Check if a user has access to an establishment."""
    if user_role == "admin":
        return {"has_access": True, "role": "admin", "is_owner": True}

    supabase = get_supabase()
    est_response = (
        supabase.table("establishments")
        .select("owner_id")
        .eq("id", establishment_id)
        .execute()
    )
    if not est_response.data:
        return {"has_access": False}

    if est_response.data[0].get("owner_id") == user_id:
        return {"has_access": True, "role": "owner", "is_owner": True}

    assignment_response = (
        supabase.table("establishment_assignments")
        .select("role")
        .eq("user_id", user_id)
        .eq("establishment_id", establishment_id)
        .execute()
    )
    if assignment_response.data:
        return {
            "has_access": True,
            "role": assignment_response.data[0].get("role"),
            "is_owner": False,
        }

    return {"has_access": False}


def require_establishment_access(allowed_roles: Optional[List[str]] = None):
    """Dependency factory: require access to an establishment."""
    async def checker(establishment_id: str, request: Request):
        user = await get_current_user(request)
        access = await check_establishment_access(user.id, establishment_id, user.role)
        if not access.get("has_access"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this establishment",
            )
        if allowed_roles and access.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient establishment permissions",
            )
        return user
    return checker


# ---- Reservation Access Control ----

async def check_reservation_access(
    user_id: str,
    reservation_id: str,
    user_role: str,
) -> Dict[str, bool]:
    """Check if a user has access to a reservation."""
    supabase = get_supabase()
    res_response = (
        supabase.table("reservations")
        .select("user_id, establishment_id")
        .eq("id", reservation_id)
        .execute()
    )
    if not res_response.data:
        return {"has_access": False, "can_modify": False}

    reservation = res_response.data[0]
    if reservation.get("user_id") == user_id:
        return {"has_access": True, "can_modify": True, "is_owner": True}

    if user_role in ("owner", "admin"):
        est_access = await check_establishment_access(
            user_id, reservation.get("establishment_id"), user_role
        )
        if est_access.get("has_access"):
            return {"has_access": True, "can_modify": True, "is_owner": False}

    return {"has_access": False, "can_modify": False}


# ---- Permission Utilities ----

def get_available_modules() -> List[Dict[str, Any]]:
    """Get list of all available modules with their actions for UI."""
    return [
        {
            "id": module,
            "label": MODULE_LABELS.get(module, module),
            "actions": [
                {"id": action, "label": ACTION_LABELS.get(action, action)}
                for action in actions
            ],
        }
        for module, actions in MODULE_ACTIONS.items()
    ]


def format_permissions_for_display(
    permissions: Dict[str, Dict[str, bool]],
) -> List[Dict[str, Any]]:
    """Format permissions for UI display."""
    return [
        {
            "module": module,
            "label": MODULE_LABELS.get(module, module),
            "actions": [
                {"action": action, "label": ACTION_LABELS.get(action, action), "granted": granted}
                for action, granted in actions.items()
            ],
        }
        for module, actions in permissions.items()
    ]
