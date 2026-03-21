from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "LibreWork API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str  # anon/public key
    SUPABASE_SERVICE_KEY: str  # service role key (for admin operations)
    
    # Stack Auth
    STACK_PROJECT_ID: str = ""
    STACK_SECRET_SERVER_KEY: str = ""
    
    # JWT (legacy — kept for reference during migration, will be removed in plan 01-05)
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # QR Code Storage
    QR_CODE_STORAGE_BUCKET: str = "qr-codes"
    
    # Credit System
    INITIAL_CREDITS: int = 10
    CREDIT_COST_PER_HOUR: int = 1
    MIN_CREDIT_COST: int = 1
    MAX_CREDIT_COST: int = 10
    
    # Cancellation Refund Policy (in minutes)
    FULL_REFUND_BEFORE_MINUTES: int = 120  # 2 hours
    PARTIAL_REFUND_BEFORE_MINUTES: int = 30  # 30 minutes
    PARTIAL_REFUND_PERCENTAGE: float = 0.5  # 50%
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # Email (Resend)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "LibreWork <onboarding@resend.dev>"

    # Search
    DEFAULT_SEARCH_RADIUS_KM: float = 10.0
    MAX_SEARCH_RESULTS: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

