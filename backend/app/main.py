from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, establishments, spaces, reservations, credits, reviews

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
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(establishments.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(spaces.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(reservations.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(credits.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(reviews.router, prefix=f"{settings.API_V1_PREFIX}")


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

