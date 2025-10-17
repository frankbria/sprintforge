"""Global test configuration and fixtures for SprintForge."""

# CRITICAL: Set environment variables BEFORE any imports
# This prevents Settings validation errors during conftest loading
import os
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing')
# Use SQLite for unit tests (no PostgreSQL required)
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///:memory:')
os.environ.setdefault('CORS_ORIGINS', '["http://testserver"]')

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import Settings, get_settings


# Test database configuration - using SQLite for unit tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_DATABASE_URL_SYNC = "sqlite:///:memory:"


class TestSettings(Settings):
    """Test-specific settings override."""

    database_url: str = TEST_DATABASE_URL
    redis_url: str = "redis://localhost:6379/15"  # Use different DB for tests
    environment: str = "testing"
    debug: bool = True
    secret_key: str = "test-secret-key-for-testing-only"

    # Disable external services for testing
    openai_api_key: str = "test-key"

    # Test-specific CORS
    cors_origins: list[str] = ["http://testserver"]


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Provide test settings."""
    return TestSettings()


@pytest.fixture(scope="session")
def override_settings(test_settings: TestSettings) -> Generator[None, None, None]:
    """Override application settings for testing."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session")
async def async_engine(test_settings: TestSettings):
    """Create async database engine for testing (SQLite in-memory)."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    async_session_maker = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
def sync_engine(test_settings: TestSettings):
    """Create synchronous database engine for testing (SQLite in-memory)."""
    engine = create_engine(
        TEST_DATABASE_URL_SYNC,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )

    yield engine

    engine.dispose()


@pytest.fixture
def client(override_settings) -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(override_settings) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = Mock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.exists.return_value = False
    redis_mock.expire.return_value = True
    return redis_mock


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-id",
        "name": "Test User",
        "email": "test@example.com",
        "email_verified": None,
        "image": None,
        "subscription_tier": "free",
        "subscription_status": "active",
        "max_projects": 3
    }


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "id": "test-project-id",
        "name": "Test Project",
        "description": "A test project for testing",
        "owner_id": "test-user-id",
        "is_public": False,
        "config": {
            "template_version": "1.0",
            "custom_fields": [],
            "workflow_settings": {
                "default_status": "todo",
                "statuses": ["todo", "in_progress", "done"]
            }
        },
        "template_checksum": "abc123"
    }


@pytest.fixture
def sample_project_membership_data():
    """Sample project membership data for testing."""
    return {
        "user_id": "test-user-id",
        "project_id": "test-project-id",
        "role": "owner",
        "permissions": ["read", "write", "admin"],
        "invitation_email": None,
        "invitation_token": None,
        "invitation_status": "accepted"
    }


# Database utilities for tests
@pytest_asyncio.fixture
async def clean_database(async_session: AsyncSession):
    """Clean database before each test."""
    # This will be implemented when we have actual models
    # For now, just ensure we have a clean slate
    yield

    # Cleanup after test
    await async_session.rollback()


# Factory fixtures for creating test data
class DatabaseFactory:
    """Factory for creating test database objects."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, **kwargs):
        """Create a test user."""
        # To be implemented when User model is available
        pass

    async def create_project(self, **kwargs):
        """Create a test project."""
        # To be implemented when Project model is available
        pass

    async def create_project_membership(self, **kwargs):
        """Create a test project membership."""
        # To be implemented when ProjectMembership model is available
        pass


@pytest_asyncio.fixture
async def db_factory(async_session: AsyncSession) -> DatabaseFactory:
    """Database factory for creating test objects."""
    return DatabaseFactory(async_session)


# HTTP Client utilities
class APITestClient:
    """Enhanced test client with utilities for API testing."""

    def __init__(self, client: TestClient):
        self.client = client
        self.auth_headers = {}

    def set_auth_headers(self, token: str):
        """Set authentication headers."""
        self.auth_headers = {"Authorization": f"Bearer {token}"}

    def get(self, url: str, **kwargs):
        """GET request with auth headers."""
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_headers)
        return self.client.get(url, headers=headers, **kwargs)

    def post(self, url: str, **kwargs):
        """POST request with auth headers."""
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_headers)
        return self.client.post(url, headers=headers, **kwargs)

    def put(self, url: str, **kwargs):
        """PUT request with auth headers."""
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_headers)
        return self.client.put(url, headers=headers, **kwargs)

    def delete(self, url: str, **kwargs):
        """DELETE request with auth headers."""
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_headers)
        return self.client.delete(url, headers=headers, **kwargs)


@pytest.fixture
def api_client(client: TestClient) -> APITestClient:
    """Enhanced API test client."""
    return APITestClient(client)


# Async HTTP Client utilities
class AsyncAPITestClient:
    """Enhanced async test client with utilities for API testing."""

    def __init__(self, client: AsyncClient):
        self.client = client
        self.auth_headers = {}

    def set_auth_headers(self, token: str):
        """Set authentication headers."""
        self.auth_headers = {"Authorization": f"Bearer {token}"}

    async def get(self, url: str, **kwargs):
        """GET request with auth headers."""
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_headers)
        return await self.client.get(url, headers=headers, **kwargs)

    async def post(self, url: str, **kwargs):
        """POST request with auth headers."""
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_headers)
        return await self.client.post(url, headers=headers, **kwargs)

    async def put(self, url: str, **kwargs):
        """PUT request with auth headers."""
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_headers)
        return await self.client.put(url, headers=headers, **kwargs)

    async def delete(self, url: str, **kwargs):
        """DELETE request with auth headers."""
        headers = kwargs.pop("headers", {})
        headers.update(self.auth_headers)
        return await self.client.delete(url, headers=headers, **kwargs)


@pytest_asyncio.fixture
async def async_api_client(async_client: AsyncClient) -> AsyncAPITestClient:
    """Enhanced async API test client."""
    return AsyncAPITestClient(async_client)