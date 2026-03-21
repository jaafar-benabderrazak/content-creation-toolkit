"""
Role-Based Access Control (RBAC) API Endpoints
Manage custom roles, permissions, and user assignments
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.core.auth_enhanced import get_current_user, get_current_admin
from app.core.rbac import (
    create_custom_role, update_custom_role, delete_custom_role,
    assign_role_to_user, resolve_user_permissions,
    get_available_modules, format_permissions_for_display,
    DEFAULT_ROLE_PERMISSIONS, MODULE_LABELS, ACTION_LABELS
)
from app.core.audit import AuditAction, log_user_action
from app.core.supabase import get_supabase
from app.schemas import UserResponse

router = APIRouter(prefix="/rbac", tags=["RBAC"])


# ============================================
# Request/Response Schemas
# ============================================

class PermissionActionSchema(BaseModel):
    action: str
    granted: bool = False


class PermissionModuleSchema(BaseModel):
    module: str
    actions: List[PermissionActionSchema]


class CustomRoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    permissions: Dict[str, Dict[str, bool]]
    color: str = Field(default="#6366f1", pattern=r"^#[0-9A-Fa-f]{6}$")


class CustomRoleUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    permissions: Optional[Dict[str, Dict[str, bool]]] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class CustomRoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    permissions: Dict[str, Dict[str, bool]]
    is_system: bool
    color: str
    created_at: str


class UserRoleAssignmentRequest(BaseModel):
    user_id: str
    role_id: Optional[str] = None  # None = remove custom role assignment


class EstablishmentAssignmentRequest(BaseModel):
    user_id: str
    establishment_id: str
    role: str = Field(..., pattern=r"^(manager|staff|viewer)$")


# ============================================
# Role Management Endpoints
# ============================================

@router.get("/roles", response_model=List[CustomRoleResponse])
async def list_custom_roles(
    include_system: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """List all custom roles."""
    supabase = get_supabase()

    query = supabase.table("custom_roles").select("*")

    if not include_system:
        query = query.eq("is_system", False)

    response = query.order("name").execute()

    return response.data or []


@router.get("/roles/{role_id}", response_model=CustomRoleResponse)
async def get_custom_role(
    role_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific custom role."""
    supabase = get_supabase()

    response = supabase.table("custom_roles").select("*").eq("id", role_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    return response.data[0]


@router.post("/roles", response_model=CustomRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: CustomRoleCreateRequest,
    current_user: dict = Depends(get_current_admin)
):
    """Create a new custom role (admin only)."""
    supabase = get_supabase()

    # Check if role name already exists
    existing = supabase.table("custom_roles").select("id").ilike("name", role_data.name).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )

    role = await create_custom_role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        color=role_data.color
    )

    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role"
        )

    # Log the action
    await log_user_action(
        user_id=current_user["id"],
        action=AuditAction.ROLE_CREATE,
        details={"role_id": role["id"], "role_name": role["name"]}
    )

    return role


@router.put("/roles/{role_id}", response_model=CustomRoleResponse)
async def update_role(
    role_id: str,
    role_data: CustomRoleUpdateRequest,
    current_user: dict = Depends(get_current_admin)
):
    """Update a custom role (admin only)."""
    supabase = get_supabase()

    # Check if role exists
    existing = supabase.table("custom_roles").select("*").eq("id", role_id).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    role = existing.data[0]

    # Prevent modification of system roles (optional protection)
    if role.get("is_system") and role_data.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify permissions of system roles"
        )

    # Check name uniqueness if changing name
    if role_data.name and role_data.name.lower() != role["name"].lower():
        name_check = supabase.table("custom_roles").select("id").ilike("name", role_data.name).execute()
        if name_check.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name already exists"
            )

    updates = {}
    if role_data.name is not None:
        updates["name"] = role_data.name
    if role_data.description is not None:
        updates["description"] = role_data.description
    if role_data.permissions is not None:
        updates["permissions"] = role_data.permissions
    if role_data.color is not None:
        updates["color"] = role_data.color

    if not updates:
        return role

    updated = await update_custom_role(role_id, updates)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )

    # Log the action
    await log_user_action(
        user_id=current_user["id"],
        action=AuditAction.ROLE_UPDATE,
        details={"role_id": role_id, "changes": list(updates.keys())}
    )

    return updated


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Delete a custom role (admin only)."""
    supabase = get_supabase()

    # Check if role exists
    existing = supabase.table("custom_roles").select("*").eq("id", role_id).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    role = existing.data[0]

    # Prevent deletion of system roles
    if role.get("is_system"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system roles"
        )

    success = await delete_custom_role(role_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete role"
        )

    # Log the action
    await log_user_action(
        user_id=current_user["id"],
        action=AuditAction.ROLE_DELETE,
        details={"role_id": role_id, "role_name": role["name"]}
    )

    return None


# ============================================
# User Role Assignment Endpoints
# ============================================

@router.post("/users/assign-role")
async def assign_role_to_user_endpoint(
    assignment: UserRoleAssignmentRequest,
    current_user: dict = Depends(get_current_admin)
):
    """Assign a custom role to a user (admin only)."""
    supabase = get_supabase()

    # Verify user exists
    user_response = supabase.table("users").select("*").eq("id", assignment.user_id).execute()
    if not user_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    target_user = user_response.data[0]

    # If role_id provided, verify it exists
    if assignment.role_id:
        role_response = supabase.table("custom_roles").select("id").eq("id", assignment.role_id).execute()
        if not role_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

    success = await assign_role_to_user(assignment.user_id, assignment.role_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role"
        )

    # Log the action
    await log_user_action(
        user_id=current_user["id"],
        action=AuditAction.USER_ROLE_ASSIGN,
        target_user_id=assignment.user_id,
        target_user_email=target_user["email"],
        details={
            "previous_role_id": target_user.get("custom_role_id"),
            "new_role_id": assignment.role_id
        }
    )

    return {"message": "Role assigned successfully"}


@router.get("/users/{user_id}/permissions", response_model=Dict[str, Any])
async def get_user_permissions(
    user_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Get resolved permissions for a user (admin only)."""
    supabase = get_supabase()

    # Verify user exists
    user_response = supabase.table("users").select("*").eq("id", user_id).execute()
    if not user_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user = user_response.data[0]
    permissions = await resolve_user_permissions(user_id)

    return {
        "user_id": user_id,
        "email": user["email"],
        "role": user["role"],
        "custom_role_id": user.get("custom_role_id"),
        "permissions": permissions,
        "permissions_display": format_permissions_for_display(permissions)
    }


# ============================================
# Establishment Assignment Endpoints
# ============================================

@router.post("/establishments/assign")
async def assign_user_to_establishment(
    assignment: EstablishmentAssignmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Assign a user to an establishment with a specific role.
    Only establishment owners or admins can do this.
    """
    supabase = get_supabase()

    # Verify establishment exists and user has permission
    est_response = supabase.table("establishments").select("*").eq("id", assignment.establishment_id).execute()
    if not est_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )

    establishment = est_response.data[0]

    # Check permission
    if current_user["role"] != "admin" and establishment["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage this establishment"
        )

    # Verify target user exists
    user_response = supabase.table("users").select("*").eq("id", assignment.user_id).execute()
    if not user_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if assignment already exists
    existing = supabase.table("establishment_assignments").select("id").eq("user_id", assignment.user_id).eq("establishment_id", assignment.establishment_id).execute()

    assignment_data = {
        "user_id": assignment.user_id,
        "establishment_id": assignment.establishment_id,
        "role": assignment.role,
        "assigned_by": current_user["id"]
    }

    if existing.data:
        # Update existing assignment
        supabase.table("establishment_assignments").update(assignment_data).eq("id", existing.data[0]["id"]).execute()
    else:
        # Create new assignment
        supabase.table("establishment_assignments").insert(assignment_data).execute()

    return {"message": "User assigned to establishment successfully"}


@router.delete("/establishments/{establishment_id}/users/{user_id}")
async def remove_user_from_establishment(
    establishment_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a user from an establishment assignment."""
    supabase = get_supabase()

    # Verify establishment exists and user has permission
    est_response = supabase.table("establishments").select("owner_id").eq("id", establishment_id).execute()
    if not est_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )

    establishment = est_response.data[0]

    # Check permission
    if current_user["role"] != "admin" and establishment["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage this establishment"
        )

    # Delete assignment
    supabase.table("establishment_assignments").delete().eq("user_id", user_id).eq("establishment_id", establishment_id).execute()

    return {"message": "User removed from establishment"}


@router.get("/establishments/{establishment_id}/users")
async def get_establishment_users(
    establishment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all users assigned to an establishment."""
    supabase = get_supabase()

    # Verify establishment exists and user has access
    est_response = supabase.table("establishments").select("owner_id").eq("id", establishment_id).execute()
    if not est_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )

    establishment = est_response.data[0]

    # Check access
    if current_user["role"] != "admin":
        # Check if user is owner or assigned
        has_access = establishment["owner_id"] == current_user["id"]
        if not has_access:
            assignment = supabase.table("establishment_assignments").select("id").eq("user_id", current_user["id"]).eq("establishment_id", establishment_id).execute()
            has_access = bool(assignment.data)

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this establishment"
            )

    # Get owner
    owner_response = supabase.table("users").select("id, email, full_name, role").eq("id", establishment["owner_id"]).execute()
    owner = owner_response.data[0] if owner_response.data else None

    # Get assigned users
    assignments_response = supabase.table("establishment_assignments").select("*, users(id, email, full_name, role)").eq("establishment_id", establishment_id).execute()

    return {
        "owner": owner,
        "assignments": assignments_response.data or []
    }


# ============================================
# Permission Metadata Endpoints
# ============================================

@router.get("/permissions/modules")
async def get_permission_modules(
    current_user: dict = Depends(get_current_user)
):
    """Get all available permission modules and actions (for UI)."""
    return get_available_modules()


@router.get("/permissions/defaults/{role}")
async def get_default_role_permissions(
    role: str,
    current_user: dict = Depends(get_current_user)
):
    """Get default permissions for a legacy role."""
    if role not in DEFAULT_ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {list(DEFAULT_ROLE_PERMISSIONS.keys())}"
        )

    permissions = DEFAULT_ROLE_PERMISSIONS[role]

    return {
        "role": role,
        "permissions": permissions,
        "display": format_permissions_for_display(permissions)
    }


@router.get("/permissions/labels")
async def get_permission_labels(
    current_user: dict = Depends(get_current_user)
):
    """Get human-readable labels for modules and actions."""
    return {
        "modules": MODULE_LABELS,
        "actions": ACTION_LABELS
    }
