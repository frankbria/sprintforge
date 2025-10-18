"""Pytest configuration with database fixtures for integration tests."""

import asyncio
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
from app.models.notification import (
    Notification,
    NotificationRule,
    NotificationLog,
    NotificationTemplate,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Ensure environment is properly configured for tests
    yield


@pytest.fixture(scope="session")
def event_loop():
    """
    Create session-scoped event loop for pytest-asyncio.

    This is required because we have session-scoped async fixtures (test_engine).
    Without this, pytest-asyncio's default function-scoped event_loop conflicts
    with session-scoped async fixtures, causing ScopeMismatch errors.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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

    # Clear rate limiter state to prevent test interference
    # The RateLimitMiddleware stores requests in instance attribute
    # We need to find and clear it
    for middleware in app.user_middleware:
        # Access the middleware instance
        if hasattr(middleware, 'kwargs'):
            # Middleware not yet instantiated, will be fresh
            pass

    # Create test client with unique headers to avoid IP rate limits
    import random
    random_ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"X-Forwarded-For": random_ip}  # Use unique IP for each test
    ) as ac:
        yield ac

    # Clean up override
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session(test_db_session: AsyncSession) -> AsyncSession:
    """Alias for test_db_session for backward compatibility."""
    return test_db_session


@pytest_asyncio.fixture
async def test_client(client: AsyncClient) -> AsyncClient:
    """Alias for client fixture for backward compatibility with test_main.py."""
    return client


@pytest_asyncio.fixture
async def test_user(test_db_session: AsyncSession):
    """Create a test user for model tests."""
    from app.models.user import User

    user = User(
        email="testuser@example.com",
        name="Test User",
        subscription_tier="free",
        subscription_status="active",
        preferences={},
        is_active=True,
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_user_pro(test_db_session: AsyncSession):
    """Create a test pro user for model tests."""
    from app.models.user import User

    user = User(
        email="prouser@example.com",
        name="Pro User",
        subscription_tier="pro",
        subscription_status="active",
        preferences={},
        is_active=True,
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_project(test_db_session: AsyncSession, test_user):
    """Create a test project for model tests."""
    from app.models.project import Project

    project = Project(
        name="Test Project",
        description="A test project",
        owner_id=test_user.id,
        configuration={
            "sprint_pattern": "YY.Q.#",
            "sprint_duration_weeks": 2,
            "working_days": [1, 2, 3, 4, 5],
        },
        template_version="1.0",
        is_public=False,
    )

    test_db_session.add(project)
    await test_db_session.commit()
    await test_db_session.refresh(project)

    return project


# Notification-specific fixtures
@pytest_asyncio.fixture
async def test_notification(test_db_session: AsyncSession, test_user):
    """Create a test notification."""
    from app.models.notification import Notification, NotificationType, NotificationStatus

    notification = Notification(
        user_id=test_user.id,
        type=NotificationType.SPRINT_COMPLETE,
        title="Test Notification",
        message="This is a test notification message",
        status=NotificationStatus.UNREAD,
        metadata={"test": True},
    )

    test_db_session.add(notification)
    await test_db_session.commit()
    await test_db_session.refresh(notification)

    return notification


@pytest_asyncio.fixture
async def test_notification_rule(test_db_session: AsyncSession, test_user):
    """Create a test notification rule."""
    from app.models.notification import (
        NotificationRule,
        NotificationType,
        NotificationChannel,
    )

    rule = NotificationRule(
        user_id=test_user.id,
        event_type=NotificationType.SPRINT_COMPLETE,
        enabled=True,
        channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        conditions={},
    )

    test_db_session.add(rule)
    await test_db_session.commit()
    await test_db_session.refresh(rule)

    return rule


@pytest_asyncio.fixture
async def test_notification_template(test_db_session: AsyncSession):
    """Create a test notification template."""
    from app.models.notification import NotificationTemplate, NotificationType

    template = NotificationTemplate(
        event_type=NotificationType.SPRINT_COMPLETE,
        subject_template="Sprint {{ sprint_name }} Complete",
        body_template_html="<p>Sprint {{ sprint_name }} completed {{ completion }}%</p>",
        body_template_text="Sprint {{ sprint_name }} completed {{ completion }}%",
    )

    test_db_session.add(template)
    await test_db_session.commit()
    await test_db_session.refresh(template)

    return template
