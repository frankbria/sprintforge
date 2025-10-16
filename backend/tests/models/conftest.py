"""Fixtures for model tests."""

import pytest_asyncio
from uuid import UUID
from sqlalchemy import String, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database.connection import Base

# SQLite-compatible UUID type decorator
class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses PostgreSQL's UUID type, otherwise uses String(36)."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, UUID):
            return value
        else:
            return UUID(value)


# Patch PostgreSQL types for SQLite testing BEFORE importing models
from sqlalchemy import JSON
from sqlalchemy.dialects import postgresql

# Store original types
_original_uuid = postgresql.UUID
_original_jsonb = postgresql.JSONB

# Replace with SQLite-compatible types
postgresql.UUID = lambda **kwargs: GUID
# JSONB needs to return actual JSON type instance, not callable
_original_jsonb_class = postgresql.JSONB
postgresql.JSONB = JSON

# Now import models AFTER patching types
import app.models.user
import app.models.project
import app.models.simulation_result

# Use SQLite in-memory for fast model tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_db_session():
    """Create a test database session with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Restore original PostgreSQL types
    postgresql.UUID = _original_uuid
    postgresql.JSONB = _original_jsonb
