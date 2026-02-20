"""
FastAPI authentication dependencies for LibreWork.
Verifies Stack Auth JWTs and resolves local user records.
"""
import jwt
from fastapi import HTTPException, Request, status

from app.core.stack_auth import verify_stack_auth_token
from app.core.supabase import get_supabase
from app.schemas import UserResponse, UserRole


async def get_current_user(request: Request) -> UserResponse:
    """Get the current authenticated user from a Stack Auth access token."""
    token = request.headers.get("x-stack-access-token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )

    try:
        payload = verify_stack_auth_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    stack_auth_id = payload.get("sub")
    if not stack_auth_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    supabase = get_supabase()
    response = (
        supabase.table("users")
        .select("*")
        .eq("stack_auth_id", stack_auth_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
        )

    return UserResponse(**response.data)


async def get_current_active_user(request: Request) -> UserResponse:
    """Alias kept for backward compatibility with existing routers."""
    return await get_current_user(request)


async def get_current_owner(request: Request) -> UserResponse:
    """Get the current user if they are an owner or admin."""
    user = await get_current_user(request)
    if user.role not in (UserRole.OWNER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Owner role required.",
        )
    return user


async def get_current_admin(request: Request) -> UserResponse:
    """Get the current user if they are an admin."""
    user = await get_current_user(request)
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required.",
        )
    return user


def verify_establishment_owner(
    establishment_owner_id: str, current_user: UserResponse
) -> bool:
    """Verify that the current user owns the establishment."""
    if current_user.role == UserRole.ADMIN:
        return True
    if establishment_owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this establishment",
        )
    return True
