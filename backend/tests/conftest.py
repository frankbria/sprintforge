"""Pytest configuration with database fixtures for integration tests."""

import pytest
import pytest_asyncio
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

# Set test environment variables BEFORE any app imports
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['CORS_ORIGINS'] = '["http://localhost:3000"]'

# Import Base and all models to register them with metadata
from app.database.connection import Base
from app.models.user import User, Account, Session, VerificationToken
from app.models.project import Project, ProjectMembership
from app.models.sync import SyncOperation
from app.models.share_link import ShareLink
from app.models.simulation_result import SimulationResult


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Ensure environment is properly configured for tests
    yield


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine (session scope - reused across tests)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session with tables (function scope - fresh per test).

    This fixture:
    1. Creates all tables before each test
    2. Provides a clean AsyncSession
    3. Drops all tables after each test for isolation
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Provide session
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

    # Clean up: drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database session override.

    This fixture is for integration tests that make HTTP calls
    and need the app to use the test database.
    """
    from app.main import app
    from app.database.connection import get_db

    # Override the database dependency to use test session
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up override
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session(test_db_session: AsyncSession) -> AsyncSession:
    """Alias for test_db_session for backward compatibility."""
    return test_db_session
