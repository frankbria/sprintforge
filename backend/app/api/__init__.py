"""API routes initialization."""

from fastapi import APIRouter

from .endpoints import auth

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router)

# Import other routers here as they are created
# from .endpoints import projects, sync

@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {"message": "SprintForge API v0.1.0"}