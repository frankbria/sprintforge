"""SprintForge FastAPI Application."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.config import settings
from app.api import api_router
from app.database.connection import (
    get_database_session,
    check_database_connection,
    initialize_database,
    shutdown_database,
)
from app.core.security import RateLimitMiddleware, SecurityHeadersMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="SprintForge API",
    description="Open-source, macro-free project management system",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    openapi_url="/openapi.json" if settings.environment == "development" else None,
)

# Security Middleware (order matters - add from innermost to outermost)
# 1. Security headers (closest to app)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate limiting
app.add_middleware(RateLimitMiddleware, default_requests=100, default_window=60)

# 3. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 4. Trusted hosts (outermost)
if settings.allowed_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )

# Routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_database_session)):
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.environment,
        "checks": {}
    }

    # Database connectivity check
    try:
        db_healthy = await check_database_connection()
        health_status["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": "Database connection successful" if db_healthy else "Database connection failed"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database check error: {str(e)}"
        }

    # Overall status based on checks
    if any(check["status"] == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"

    return health_status


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("SprintForge API starting up")

    # Initialize database connections
    try:
        await initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("SprintForge API shutting down")

    # Shutdown database connections
    try:
        await shutdown_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Database shutdown error", error=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
        log_config=None,  # Use structlog instead
    )