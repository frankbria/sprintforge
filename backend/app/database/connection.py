"""
Database connection management for SprintForge.
"""

import asyncio
from typing import AsyncGenerator

import asyncpg
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from backend.app.core.config import get_settings

logger = structlog.get_logger(__name__)

# SQLAlchemy base for models
Base = declarative_base()

# Global variables for connection management
_engine = None
_session_factory = None


def get_database_url() -> str:
    """Get database URL from settings."""
    settings = get_settings()
    return settings.database_url


def create_engine():
    """Create SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        database_url = get_database_url()
        settings = get_settings()

        _engine = create_async_engine(
            database_url,
            echo=settings.debug,  # Log SQL queries in debug mode
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections every hour
        )

    return _engine


def get_session_factory():
    """Get SQLAlchemy session factory."""
    global _session_factory
    if _session_factory is None:
        engine = create_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    return _session_factory


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide database session to FastAPI endpoints.

    Usage:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_database_session)):
            # Use db session here
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        engine = create_engine()
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            row = result.fetchone()
            return row[0] == 1
    except Exception as e:
        logger.error("Database connection check failed", error=str(e))
        return False


async def get_raw_connection() -> asyncpg.Connection:
    """Get raw asyncpg connection for migrations and direct queries."""
    database_url = get_database_url()

    # Convert SQLAlchemy URL to asyncpg format if needed
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    return await asyncpg.connect(database_url)


async def close_database_connections():
    """Close all database connections (for application shutdown)."""
    global _engine, _session_factory

    if _engine:
        await _engine.dispose()
        _engine = None

    _session_factory = None
    logger.info("Database connections closed")


# Database startup and shutdown handlers
async def initialize_database():
    """Initialize database connections on startup."""
    logger.info("Initializing database connections")

    # Test connection
    if await check_database_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
        raise RuntimeError("Could not connect to database")


async def shutdown_database():
    """Shutdown database connections."""
    logger.info("Shutting down database connections")
    await close_database_connections()