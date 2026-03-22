from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import (
    auth, auth_enhanced, establishments, spaces, reservations, credits, reviews, users, owner, debug,
    favorites, activity, groups, loyalty, notifications, calendar, rbac, admin_audit, payments
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(debug.router, prefix=f"{settings.API_V1_PREFIX}")
# Legacy auth router (kept for backward compatibility)
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}")
# Enhanced auth router (new CivilDocPro-style authentication)
app.include_router(auth_enhanced.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(owner.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(establishments.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(spaces.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(reservations.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(credits.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(reviews.router, prefix=f"{settings.API_V1_PREFIX}")

# New feature routers
app.include_router(favorites.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(activity.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(groups.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(loyalty.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(notifications.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(calendar.router, prefix=f"{settings.API_V1_PREFIX}")

# RBAC and Admin routers (new enhanced auth system)
app.include_router(rbac.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(admin_audit.router, prefix=f"{settings.API_V1_PREFIX}")

# Payments router (Stripe Checkout)
app.include_router(payments.router, prefix=f"{settings.API_V1_PREFIX}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to LibreWork API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

