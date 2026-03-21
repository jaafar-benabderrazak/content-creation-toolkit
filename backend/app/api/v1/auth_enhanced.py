"""
Enhanced Authentication API Endpoints for LibreWork
Based on CivilDocPro architecture - Custom JWT + RBAC + Audit Logging
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field

from app.core.auth_enhanced import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    generate_reset_token, hash_reset_token, verify_reset_token,
    get_user_by_email, get_user_by_id, authenticate_user,
    get_current_user, get_current_admin
)
from app.core.rbac import UserRole, resolve_user_permissions
from app.core.audit import (
    AuditAction, log_auth_action, log_user_action,
    get_user_audit_logs, get_recent_audit_logs
)
from app.core.supabase import get_supabase
from app.core.email import send_email  # Assume this exists
from app.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================
# Request/Response Schemas
# ============================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    role: UserRole = UserRole.CUSTOMER
    phone_number: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None


class PermissionsResponse(BaseModel):
    permissions: dict
    role: str
    custom_role_id: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_label: Optional[str]
    created_at: datetime
    ip_address: Optional[str]


# ============================================
# Registration
# ============================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: RegisterRequest,
    background_tasks: BackgroundTasks
):
    """Register a new user with custom authentication."""
    supabase = get_supabase()
    client_info = get_client_info(request)

    # Check if email already exists
    existing = await get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    user_data_dict = {
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": user_data.role.value,
        "hashed_password": hashed_password,
        "coffee_credits": 10,  # Welcome bonus
        "is_active": True,
        "is_verified": False,
        "phone_number": user_data.phone_number,
    }

    try:
        response = supabase.table("users").insert(user_data_dict).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

        user = response.data[0]

        # Log the registration
        background_tasks.add_task(
            log_auth_action,
            user_id=user["id"],
            action=AuditAction.AUTH_REGISTER,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            details={"email": user_data.email, "role": user_data.role.value}
        )

        return UserResponse(**user)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


# ============================================
# Login
# ============================================

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    background_tasks: BackgroundTasks
):
    """Login with email and password."""
    client_info = get_client_info(request)

    # Authenticate user
    user = await authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Update last login
    supabase = get_supabase()
    supabase.table("users").update({
        "last_login_at": datetime.utcnow().isoformat(),
        "login_count": user.get("login_count", 0) + 1
    }).eq("id", user["id"]).execute()

    # Create tokens
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Log the login
    background_tasks.add_task(
        log_auth_action,
        user_id=user["id"],
        action=AuditAction.AUTH_LOGIN,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"]
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        user=UserResponse(**user)
    )


# ============================================
# Token Refresh
# ============================================

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_request: RefreshRequest):
    """Refresh access token using refresh token."""
    payload = decode_token(refresh_request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user still exists and is active
    user = await get_user_by_id(user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=1800,
        user=UserResponse(**user)
    )


# ============================================
# Current User
# ============================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserResponse(**current_user)


@router.get("/me/permissions", response_model=PermissionsResponse)
async def get_current_user_permissions(current_user: dict = Depends(get_current_user)):
    """Get current user's resolved permissions."""
    user_id = current_user["id"]
    permissions = await resolve_user_permissions(user_id)

    return PermissionsResponse(
        permissions=permissions,
        role=current_user["role"],
        custom_role_id=current_user.get("custom_role_id")
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: Request,
    user_update: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Update current user information."""
    supabase = get_supabase()
    client_info = get_client_info(request)

    # Build update data
    update_data = {}
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    if user_update.email is not None:
        # Check if email is already taken
        if user_update.email != current_user["email"]:
            existing = await get_user_by_email(user_update.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        update_data["email"] = user_update.email
    if user_update.phone_number is not None:
        update_data["phone_number"] = user_update.phone_number
    if user_update.avatar_url is not None:
        update_data["avatar_url"] = user_update.avatar_url

    if not update_data:
        return UserResponse(**current_user)

    try:
        # Store previous value for audit
        previous_value = {k: current_user.get(k) for k in update_data.keys()}

        response = supabase.table("users").update(update_data).eq("id", current_user["id"]).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed"
            )

        updated_user = response.data[0]

        # Log the update
        if background_tasks:
            background_tasks.add_task(
                log_user_action,
                user_id=current_user["id"],
                action=AuditAction.USER_UPDATE,
                target_user_id=current_user["id"],
                target_user_email=current_user["email"],
                previous_value=previous_value,
                new_value=update_data,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"]
            )

        return UserResponse(**updated_user)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update failed: {str(e)}"
        )


# ============================================
# Password Management
# ============================================

@router.post("/password/change")
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Change current user's password."""
    supabase = get_supabase()
    client_info = get_client_info(request)

    # Verify current password
    if not verify_password(password_data.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash new password
    new_hashed_password = hash_password(password_data.new_password)

    try:
        supabase.table("users").update({
            "hashed_password": new_hashed_password,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", current_user["id"]).execute()

        # Log the password change
        if background_tasks:
            background_tasks.add_task(
                log_auth_action,
                user_id=current_user["id"],
                action=AuditAction.AUTH_PASSWORD_CHANGE,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"]
            )

        return {"message": "Password changed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )


@router.post("/password/reset-request")
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks
):
    """Request a password reset (sends email with token)."""
    client_info = get_client_info(request)

    user = await get_user_by_email(reset_request.email)

    # Always return success even if email doesn't exist (security)
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}

    # Generate reset token
    reset_token = generate_reset_token()
    token_hash = hash_reset_token(reset_token)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Store hashed token
    supabase = get_supabase()
    supabase.table("users").update({
        "reset_token_hash": token_hash,
        "reset_token_expires": expires_at.isoformat()
    }).eq("id", user["id"]).execute()

    # Log the request
    background_tasks.add_task(
        log_auth_action,
        user_id=user["id"],
        action=AuditAction.AUTH_PASSWORD_RESET_REQUEST,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"]
    )

    # Send email (in production, this would send an actual email)
    # For now, just log it
    print(f"[PASSWORD RESET] User: {user['email']}, Token: {reset_token}")

    # TODO: Implement actual email sending
    # background_tasks.add_task(
    #     send_password_reset_email,
    #     email=user["email"],
    #     token=reset_token
    # )

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password/reset-confirm")
async def confirm_password_reset(
    request: Request,
    reset_confirm: PasswordResetConfirmRequest,
    background_tasks: BackgroundTasks
):
    """Confirm password reset with token."""
    supabase = get_supabase()
    client_info = get_client_info(request)

    token_hash = hash_reset_token(reset_confirm.token)
    now = datetime.utcnow().isoformat()

    # Find user with valid token
    response = supabase.table("users").select("*").eq("reset_token_hash", token_hash).gt("reset_token_expires", now).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user = response.data[0]

    # Hash new password
    new_hashed_password = hash_password(reset_confirm.new_password)

    # Update password and clear reset token
    supabase.table("users").update({
        "hashed_password": new_hashed_password,
        "reset_token_hash": None,
        "reset_token_expires": None,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", user["id"]).execute()

    # Log the reset
    background_tasks.add_task(
        log_auth_action,
        user_id=user["id"],
        action=AuditAction.AUTH_PASSWORD_RESET,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"]
    )

    return {"message": "Password reset successfully"}


# ============================================
# Audit Log Endpoints
# ============================================

@router.get("/me/audit-logs", response_model=list[AuditLogResponse])
async def get_my_audit_logs(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's audit logs."""
    logs = await get_user_audit_logs(current_user["id"], limit, offset)
    return logs


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_all_audit_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_admin)
):
    """Get all audit logs (admin only)."""
    logs = await get_recent_audit_logs(limit, offset)
    return logs


# ============================================
# Helper Functions
# ============================================

def get_client_info(request: Request) -> dict:
    """Extract client IP and user agent from request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        real_ip = request.headers.get("X-Real-IP")
        ip_address = real_ip if real_ip else (request.client.host if request.client else "unknown")

    user_agent = request.headers.get("User-Agent", "unknown")

    return {
        "ip_address": ip_address,
        "user_agent": user_agent
    }
