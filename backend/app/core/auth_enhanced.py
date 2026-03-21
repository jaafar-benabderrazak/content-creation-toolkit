"""
Enhanced Authentication System for LibreWork
Based on CivilDocPro architecture - Custom JWT + RBAC + Audit Logging
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib
from app.core.config import settings
from app.core.supabase import get_supabase

# Password hashing configuration (same as CivilDocPro - 12 rounds)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
security = HTTPBearer()

# ============================================
# Password utilities
# ============================================

def hash_password(password: str) -> str:
    """Hash a plain password with bcrypt (12 salt rounds)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# JWT utilities
# ============================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token (30 min expiry like CivilDocPro)."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token (7 days expiry)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> dict:
    """Decode access token with error handling."""
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    return payload


# ============================================
# Password Reset utilities (like CivilDocPro)
# ============================================

def generate_reset_token() -> str:
    """Generate a secure random token for password reset."""
    return secrets.token_hex(32)


def hash_reset_token(token: str) -> str:
    """Hash the reset token for storage (SHA-256)."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_reset_token(provided_token: str, stored_hash: str) -> bool:
    """Verify a reset token against its hash."""
    return hash_reset_token(provided_token) == stored_hash


# ============================================
# User utilities
# ============================================

async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email address."""
    supabase = get_supabase()
    response = supabase.table("users").select("*").eq("email", email).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    supabase = get_supabase()
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(email)
    if not user:
        return None

    # Check if user has a password set (migration from Supabase Auth)
    hashed_password = user.get("hashed_password")
    if not hashed_password:
        return None

    if not verify_password(password, hashed_password):
        return None

    # Check if user is active
    if not user.get("is_active", True):
        return None

    return user


# ============================================
# FastAPI Dependencies
# ============================================

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract user ID from JWT token."""
    payload = decode_access_token(credentials.credentials)
    user_id: str = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    return user_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get the current authenticated user."""
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current active user."""
    return current_user


# ============================================
# Role checking dependencies
# ============================================

from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    OWNER = "owner"
    ADMIN = "admin"


async def get_current_owner(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current user if they are owner or admin."""
    if current_user.get("role") not in [UserRole.OWNER.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Owner role required.",
        )
    return current_user


async def get_current_admin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current user if they are admin."""
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required.",
        )
    return current_user


# ============================================
# Client IP and User Agent extraction
# ============================================

def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client IP and user agent from request."""
    # Get IP address
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            ip_address = real_ip
        else:
            ip_address = request.client.host if request.client else "unknown"

    # Get user agent
    user_agent = request.headers.get("User-Agent", "unknown")

    return {
        "ip_address": ip_address,
        "user_agent": user_agent
    }


# ============================================
# Optional auth middleware (for public routes that need user context)
# ============================================

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Get user if authenticated, otherwise None."""
    if not credentials:
        return None

    try:
        payload = decode_token(credentials.credentials)
        if not payload or payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await get_user_by_id(user_id)
        if user and user.get("is_active", True):
            return user
        return None
    except:
        return None
