"""
Pytest configuration and fixtures for SprintForge backend tests.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.config import get_settings
from backend.app.database.connection import get_database_session, Base
from backend.app.models import User, Project, ProjectMembership


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://sprintforge:sprintforge_dev@localhost:5432/sprintforge_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        # Start a transaction
        transaction = await session.begin()

        try:
            yield session
        finally:
            # Rollback transaction to ensure test isolation
            await transaction.rollback()
            await session.close()


@pytest_asyncio.fixture
async def test_client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database dependency override."""

    def override_get_db():
        return test_db_session

    app.dependency_overrides[get_database_session] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        subscription_tier="free",
        subscription_status="active",
        preferences={"theme": "light"},
        is_active=True,
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_user_pro(test_db_session: AsyncSession) -> User:
    """Create a test pro user."""
    user = User(
        id=uuid4(),
        email="pro@example.com",
        name="Pro User",
        subscription_tier="pro",
        subscription_status="active",
        preferences={"theme": "dark"},
        is_active=True,
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_project(test_db_session: AsyncSession, test_user: User) -> Project:
    """Create a test project."""
    project = Project(
        id=uuid4(),
        name="Test Project",
        description="A test project for SprintForge",
        owner_id=test_user.id,
        configuration={
            "sprint_pattern": "YY.Q.#",
            "sprint_duration_weeks": 2,
            "working_days": [1, 2, 3, 4, 5],
            "features": {"monte_carlo": True, "critical_path": True}
        },
        template_version="1.0",
        is_public=False,
    )

    test_db_session.add(project)
    await test_db_session.commit()
    await test_db_session.refresh(project)

    return project


@pytest_asyncio.fixture
async def test_public_project(test_db_session: AsyncSession, test_user: User) -> Project:
    """Create a test public project."""
    project = Project(
        id=uuid4(),
        name="Public Test Project",
        description="A public test project",
        owner_id=test_user.id,
        configuration={
            "sprint_pattern": "PI-N.Sprint-M",
            "sprint_duration_weeks": 3,
            "working_days": [1, 2, 3, 4, 5],
            "features": {"monte_carlo": False, "critical_path": True}
        },
        template_version="1.0",
        is_public=True,
        public_share_token="test-share-token-123",
    )

    test_db_session.add(project)
    await test_db_session.commit()
    await test_db_session.refresh(project)

    return project


@pytest.fixture
def sample_project_config():
    """Sample project configuration for testing."""
    return {
        "project_name": "Sample Project",
        "sprint_pattern": "YY.Q.#",
        "sprint_duration_weeks": 2,
        "working_days": [1, 2, 3, 4, 5],
        "holidays": ["2024-12-25", "2024-01-01"],
        "features": {
            "monte_carlo": True,
            "critical_path": True,
            "resource_leveling": False,
            "progress_tracking": True
        },
        "template_options": {
            "methodology": "agile",
            "complexity": "advanced"
        }
    }


# Test data factories
class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create_user_data(
        email: str = None,
        name: str = None,
        subscription_tier: str = "free",
        **kwargs
    ) -> dict:
        """Create user data for testing."""
        return {
            "email": email or f"user{uuid4().hex[:8]}@example.com",
            "name": name or f"User {uuid4().hex[:8]}",
            "subscription_tier": subscription_tier,
            "subscription_status": "active",
            "preferences": {"theme": "light"},
            "is_active": True,
            **kwargs
        }


class ProjectFactory:
    """Factory for creating test projects."""

    @staticmethod
    def create_project_data(
        name: str = None,
        owner_id: str = None,
        is_public: bool = False,
        **kwargs
    ) -> dict:
        """Create project data for testing."""
        return {
            "name": name or f"Project {uuid4().hex[:8]}",
            "description": "Test project description",
            "owner_id": owner_id,
            "configuration": {
                "sprint_pattern": "YY.Q.#",
                "sprint_duration_weeks": 2,
                "working_days": [1, 2, 3, 4, 5],
                "features": {"monte_carlo": True}
            },
            "template_version": "1.0",
            "is_public": is_public,
            **kwargs
        }


# Helper assertions
def assert_user_data(user: User, expected_data: dict):
    """Assert user data matches expectations."""
    assert user.email == expected_data["email"]
    assert user.name == expected_data["name"]
    assert user.subscription_tier == expected_data["subscription_tier"]
    assert user.is_active == expected_data["is_active"]


def assert_project_data(project: Project, expected_data: dict):
    """Assert project data matches expectations."""
    assert project.name == expected_data["name"]
    assert project.description == expected_data["description"]
    assert project.owner_id == expected_data["owner_id"]
    assert project.is_public == expected_data["is_public"]