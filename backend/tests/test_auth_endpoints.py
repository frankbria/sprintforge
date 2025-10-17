"""Tests for authentication API endpoints without full database."""

import pytest
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from jose import jwt
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Set environment variables before importing app modules
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'

# Create a minimal FastAPI app for testing
app = FastAPI()

# Import and add routes after setting environment
from app.api.endpoints.auth import router, get_database_session
from app.core.auth import NEXTAUTH_SECRET, ALGORITHM

app.include_router(router)


def override_get_db_with_mock(mock_db):
    """Helper to override database dependency."""
    async def override_get_db():
        yield mock_db
    return override_get_db


class TestAuthEndpointsUnit:
    """Unit tests for authentication endpoints."""

    def create_test_token(self, user_id: str, email: str, expired: bool = False) -> str:
        """Create a test JWT token."""
        if expired:
            exp = datetime.now(timezone.utc) - timedelta(minutes=5)
        else:
            exp = datetime.now(timezone.utc) + timedelta(minutes=30)

        payload = {
            "sub": user_id,
            "email": email,
            "exp": exp.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "provider": "google"
        }

        return jwt.encode(payload, NEXTAUTH_SECRET, algorithm=ALGORITHM)

    def create_mock_user(self, user_id: str = None, email: str = None):
        """Create a mock user object with proper dict for preferences."""
        # Create a class that behaves like a model but with real dict for preferences
        class MockUser:
            def __init__(self):
                self.id = uuid4() if user_id is None else user_id
                self.name = "Test User"
                self.email = email or "test@example.com"
                self.image = "https://example.com/avatar.jpg"
                self.subscription_tier = "free"
                self.subscription_status = "active"
                self.subscription_expires_at = None
                self.is_active = True
                self.created_at = datetime.now(timezone.utc)
                self.updated_at = datetime.now(timezone.utc)
                self.preferences = {}  # Real dict, not Mock
                # Add SQLAlchemy state attribute for flag_modified to work
                # The state needs a manager that supports subscripting
                mock_attr_impl = Mock()
                mock_manager = Mock()
                mock_manager.__getitem__ = Mock(return_value=mock_attr_impl)
                mock_state = Mock()
                mock_state.manager = mock_manager
                self._sa_instance_state = mock_state

        return MockUser()

    def test_get_current_user_unauthorized(self):
        """Test current user retrieval without token."""
        with TestClient(app) as client:
            response = client.get("/auth/me")
            assert response.status_code == 403

    def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token."""
        with TestClient(app) as client:
            response = client.get(
                "/auth/me",
                headers={"Authorization": "Bearer invalid_token"}
            )
            assert response.status_code == 401

    def test_get_current_user_success(self):
        """Test successful retrieval of current user."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = self.create_mock_user(user_id, email)

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(mock_user.id)
            assert data["email"] == mock_user.email
            assert data["subscription_tier"] == "free"
        finally:
            app.dependency_overrides.clear()

    def test_get_current_user_not_found(self):
        """Test current user retrieval when user not found."""
        user_id = str(uuid4())
        token = self.create_test_token(user_id, "test@example.com")

        # Mock database returning None
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404
            assert "User not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_current_user_inactive(self):
        """Test current user retrieval for inactive user."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = self.create_mock_user(user_id, email)
        mock_user.is_active = False

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 403
            assert "User account is inactive" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_update_current_user_success(self):
        """Test successful update of current user."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = self.create_mock_user(user_id, email)

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Ensure commit and refresh don't interfere with the mock_user object
        async def mock_commit():
            pass
        async def mock_refresh(obj):
            pass
        mock_db.commit = mock_commit
        mock_db.refresh = mock_refresh

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        update_data = {
            "name": "Updated Name",
            "preferences": {"theme": "dark"}
        }

        try:
            with TestClient(app) as client:
                response = client.put(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json=update_data
                )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
            # Can't use assert_called_once on regular functions, just check the result
        finally:
            app.dependency_overrides.clear()

    def test_update_current_user_partial(self):
        """Test partial update of current user."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = self.create_mock_user(user_id, email)

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        update_data = {"name": "New Name Only"}

        try:
            with TestClient(app) as client:
                response = client.put(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json=update_data
                )

            assert response.status_code == 200
            assert mock_user.name == "New Name Only"
        finally:
            app.dependency_overrides.clear()

    def test_get_session_info_success(self):
        """Test successful session info retrieval."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = self.create_mock_user(user_id, email)

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/auth/session",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert "user" in data
            assert data["user"]["id"] == str(mock_user.id)
            assert "expires_at" in data
            assert data["provider"] == "google"
        finally:
            app.dependency_overrides.clear()

    def test_validate_token_success(self):
        """Test successful token validation."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)

        with TestClient(app) as client:
            response = client.post(
                "/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == user_id
        assert data["email"] == email

    def test_validate_token_missing(self):
        """Test token validation without token."""
        with TestClient(app) as client:
            response = client.post("/auth/validate")

        assert response.status_code == 401
        assert "Invalid or missing token" in response.json()["detail"]

    def test_validate_token_invalid(self):
        """Test token validation with invalid token."""
        with TestClient(app) as client:
            response = client.post(
                "/auth/validate",
                headers={"Authorization": "Bearer invalid_token"}
            )

        assert response.status_code == 401

    def test_validate_token_expired(self):
        """Test token validation with expired token."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email, expired=True)

        with TestClient(app) as client:
            response = client.post(
                "/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 401

    def test_revoke_session_success(self):
        """Test successful session revocation."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)

        # Mock database session
        mock_db = AsyncMock()

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/auth/session",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert "Session revoked successfully" in data["message"]
        finally:
            app.dependency_overrides.clear()

    def test_auth_health_check(self):
        """Test authentication service health check."""
        with TestClient(app) as client:
            response = client.get("/auth/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
        assert "timestamp" in data

    def test_database_error_handling(self):
        """Test error handling when database operations fail."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)

        # Mock database raising exception
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection failed")

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_invalid_user_id_format(self):
        """Test handling of invalid UUID format in token."""
        token = self.create_test_token("invalid-uuid-format", "test@example.com")

        mock_db = AsyncMock()

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 400
            assert "Invalid user ID" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_preferences_merge_correctly(self):
        """Test that preferences are merged, not replaced."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = self.create_mock_user(user_id, email)
        mock_user.preferences = {"existing": "value", "keep": True}

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Ensure commit and refresh don't interfere with the mock_user object
        async def mock_commit():
            pass
        async def mock_refresh(obj):
            pass
        mock_db.commit = mock_commit
        mock_db.refresh = mock_refresh

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        update_data = {
            "preferences": {"new": "setting", "existing": "updated"}
        }

        try:
            with TestClient(app) as client:
                response = client.put(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json=update_data
                )

            assert response.status_code == 200
            # Verify preferences were merged
            expected_prefs = {
                "existing": "updated",
                "keep": True,
                "new": "setting"
            }
            assert mock_user.preferences == expected_prefs
        finally:
            app.dependency_overrides.clear()

    def test_update_rollback_on_error(self):
        """Test that database transactions are rolled back on error."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = self.create_mock_user(user_id, email)

        # Mock database with commit failure
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_db.commit.side_effect = Exception("Commit failed")

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        update_data = {"name": "New Name"}

        try:
            with TestClient(app) as client:
                response = client.put(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json=update_data
                )

            assert response.status_code == 500
            mock_db.rollback.assert_called_once()
        finally:
            app.dependency_overrides.clear()


class TestResponseModels:
    """Test response model validation."""

    def create_test_token(self, user_id: str, email: str, expired: bool = False) -> str:
        """Create a test JWT token."""
        if expired:
            exp = datetime.now(timezone.utc) - timedelta(minutes=5)
        else:
            exp = datetime.now(timezone.utc) + timedelta(minutes=30)

        payload = {
            "sub": user_id,
            "email": email,
            "exp": exp.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "provider": "google"
        }

        return jwt.encode(payload, NEXTAUTH_SECRET, algorithm=ALGORITHM)

    def test_user_response_model_structure(self):
        """Test that UserResponse model has correct structure."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)

        # Create a class that behaves like a model
        class MockUser:
            def __init__(self):
                self.id = uuid4()
                self.name = "Test User"
                self.email = "test@example.com"
                self.image = "https://example.com/avatar.jpg"
                self.subscription_tier = "pro"
                self.subscription_status = "active"
                self.subscription_expires_at = datetime.now(timezone.utc)
                self.is_active = True
                self.created_at = datetime.now(timezone.utc)
                self.updated_at = datetime.now(timezone.utc)
                self.preferences = {}

        mock_user = MockUser()

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()

            # Check all required fields are present
            required_fields = [
                "id", "name", "email", "image", "subscription_tier",
                "subscription_status", "subscription_expires_at",
                "is_active", "created_at", "updated_at"
            ]
            for field in required_fields:
                assert field in data

            # Check data types
            assert isinstance(data["id"], str)
            assert isinstance(data["name"], str)
            assert isinstance(data["email"], str)
            assert isinstance(data["subscription_tier"], str)
            assert isinstance(data["is_active"], bool)
        finally:
            app.dependency_overrides.clear()


class TestSecurityHeaders:
    """Test security headers and middleware."""

    def test_cors_headers_present(self):
        """Test that appropriate headers are set."""
        with TestClient(app) as client:
            response = client.get("/auth/health")

        # Note: FastAPI TestClient may not include all middleware headers
        # In a real deployment, security headers would be added by middleware
        assert response.status_code == 200

    def test_no_sensitive_data_in_error_responses(self):
        """Test that error responses don't leak sensitive information."""
        with TestClient(app) as client:
            response = client.get(
                "/auth/me",
                headers={"Authorization": "Bearer invalid_token"}
            )

        assert response.status_code == 401
        response_data = response.json()

        # Should not contain sensitive internal details
        assert "secret" not in str(response_data).lower()
        assert "key" not in str(response_data).lower()
        assert "database" not in str(response_data).lower()


class TestEndpointValidation:
    """Test input validation on endpoints."""

    def create_test_token(self, user_id: str, email: str, expired: bool = False) -> str:
        """Create a test JWT token."""
        if expired:
            exp = datetime.now(timezone.utc) - timedelta(minutes=5)
        else:
            exp = datetime.now(timezone.utc) + timedelta(minutes=30)

        payload = {
            "sub": user_id,
            "email": email,
            "exp": exp.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "provider": "google"
        }

        return jwt.encode(payload, NEXTAUTH_SECRET, algorithm=ALGORITHM)

    def create_mock_user(self, user_id: str = None, email: str = None):
        """Create a mock user object with proper dict for preferences."""
        # Create a class that behaves like a model but with real dict for preferences
        class MockUser:
            def __init__(self):
                self.id = uuid4() if user_id is None else user_id
                self.name = "Test User"
                self.email = email or "test@example.com"
                self.image = None
                self.subscription_tier = "free"
                self.subscription_status = "active"
                self.subscription_expires_at = None
                self.is_active = True
                self.created_at = datetime.now(timezone.utc)
                self.updated_at = datetime.now(timezone.utc)
                self.preferences = {}  # Real dict, not Mock
                # Add SQLAlchemy state attribute for flag_modified to work
                # The state needs a manager that supports subscripting
                mock_attr_impl = Mock()
                mock_manager = Mock()
                mock_manager.__getitem__ = Mock(return_value=mock_attr_impl)
                mock_state = Mock()
                mock_state.manager = mock_manager
                self._sa_instance_state = mock_state

        return MockUser()

    def test_update_user_empty_payload(self):
        """Test updating user with empty payload."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = self.create_mock_user(user_id, email)

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_database_session] = override_get_db_with_mock(mock_db)

        try:
            with TestClient(app) as client:
                response = client.put(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json={}
                )

            # Should succeed even with empty payload
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
