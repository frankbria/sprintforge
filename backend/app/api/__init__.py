"""API routes initialization."""

from fastapi import APIRouter

from .endpoints import auth, projects, excel, sharing, simulation, excel_workflow, analytics

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router)

# Include project management routes
api_router.include_router(projects.router)

# Include Excel generation routes
api_router.include_router(excel.router)

# Include Excel workflow routes (Monte Carlo integration)
api_router.include_router(excel_workflow.router)

# Include sharing routes
api_router.include_router(sharing.router)

# Include Monte Carlo simulation routes
api_router.include_router(simulation.router)

# Include analytics routes
api_router.include_router(analytics.router)

@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {"message": "SprintForge API v0.1.0"}