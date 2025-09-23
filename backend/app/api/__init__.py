"""API routes initialization."""

from fastapi import APIRouter

api_router = APIRouter()

# Import routers here as they are created
# from .endpoints import projects, auth, sync

@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {"message": "SprintForge API v0.1.0"}