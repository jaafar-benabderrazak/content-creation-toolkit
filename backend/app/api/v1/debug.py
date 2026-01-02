from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/debug/config")
async def get_config():
    """Debug endpoint to check configuration."""
    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_key_prefix": settings.SUPABASE_KEY[:30] + "..." if settings.SUPABASE_KEY else "MISSING",
        "jwt_secret_prefix": settings.JWT_SECRET_KEY[:10] + "..." if settings.JWT_SECRET_KEY else "MISSING"
    }

