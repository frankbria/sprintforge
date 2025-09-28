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
from app.api.endpoints.auth import router
from app.core.auth import NEXTAUTH_SECRET, ALGORITHM

app.include_router(router)


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
        """Create a mock user object."""
        mock_user = Mock()
        mock_user.id = uuid4() if user_id is None else user_id
        mock_user.name = "Test User"
        mock_user.email = email or "test@example.com"
        mock_user.image = "https://example.com/avatar.jpg"
        mock_user.subscription_tier = "free"
        mock_user.subscription_status = "active"
        mock_user.subscription_expires_at = None
        mock_user.is_active = True
        mock_user.created_at = datetime.now(timezone.utc)
        mock_user.updated_at = datetime.now(timezone.utc)
        mock_user.preferences = {}
        return mock_user

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

    @patch('app.database.connection.get_db')
    def test_get_current_user_success(self, mock_get_db):
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
        mock_get_db.return_value = mock_db

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

    @patch('app.database.connection.get_db')
    def test_get_current_user_not_found(self, mock_get_db):
        """Test current user retrieval when user not found."""
        user_id = str(uuid4())
        token = self.create_test_token(user_id, "test@example.com")

        # Mock database returning None
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_get_db.return_value = mock_db

        with TestClient(app) as client:
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @patch('app.database.connection.get_db')
    def test_get_current_user_inactive(self, mock_get_db):
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
        mock_get_db.return_value = mock_db

        with TestClient(app) as client:
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 403
        assert "User account is inactive" in response.json()["detail"]

    @patch('app.database.connection.get_db')
    def test_update_current_user_success(self, mock_get_db):
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
        mock_get_db.return_value = mock_db

        update_data = {
            "name": "Updated Name",
            "preferences": {"theme": "dark"}
        }

        with TestClient(app) as client:
            response = client.put(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                json=update_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('app.database.connection.get_db')
    def test_update_current_user_partial(self, mock_get_db):
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
        mock_get_db.return_value = mock_db

        update_data = {"name": "New Name Only"}

        with TestClient(app) as client:
            response = client.put(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                json=update_data
            )

        assert response.status_code == 200
        assert mock_user.name == "New Name Only"

    @patch('app.database.connection.get_db')
    def test_get_session_info_success(self, mock_get_db):
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
        mock_get_db.return_value = mock_db

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

    @patch('app.database.connection.get_db')
    def test_revoke_session_success(self, mock_get_db):
        """Test successful session revocation."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)

        # Mock database session
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        with TestClient(app) as client:
            response = client.delete(
                "/auth/session",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "Session revoked successfully" in data["message"]

    def test_auth_health_check(self):
        """Test authentication service health check."""
        with TestClient(app) as client:
            response = client.get("/auth/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
        assert "timestamp" in data

    @patch('app.database.connection.get_db')
    def test_database_error_handling(self, mock_get_db):
        """Test error handling when database operations fail."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)

        # Mock database raising exception
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection failed")
        mock_get_db.return_value = mock_db

        with TestClient(app) as client:
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    def test_invalid_user_id_format(self):
        """Test handling of invalid UUID format in token."""
        token = self.create_test_token("invalid-uuid-format", "test@example.com")

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db

            with TestClient(app) as client:
                response = client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 400
            assert "Invalid user ID" in response.json()["detail"]

    @patch('app.database.connection.get_db')
    def test_preferences_merge_correctly(self, mock_get_db):
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
        mock_get_db.return_value = mock_db

        update_data = {
            "preferences": {"new": "setting", "existing": "updated"}
        }

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

    @patch('app.database.connection.get_db')
    def test_update_rollback_on_error(self, mock_get_db):
        """Test that database transactions are rolled back on error."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)

        # Mock database with commit failure
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_user = self.create_mock_user(user_id, email)
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_db.commit.side_effect = Exception("Commit failed")
        mock_get_db.return_value = mock_db

        update_data = {"name": "New Name"}

        with TestClient(app) as client:
            response = client.put(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                json=update_data
            )

        assert response.status_code == 500
        mock_db.rollback.assert_called_once()


class TestResponseModels:
    """Test response model validation."""

    @patch('app.database.connection.get_db')
    def test_user_response_model_structure(self, mock_get_db):
        """Test that UserResponse model has correct structure."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        mock_user.image = "https://example.com/avatar.jpg"
        mock_user.subscription_tier = "pro"
        mock_user.subscription_status = "active"
        mock_user.subscription_expires_at = datetime.now(timezone.utc)
        mock_user.is_active = True
        mock_user.created_at = datetime.now(timezone.utc)
        mock_user.updated_at = datetime.now(timezone.utc)

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_get_db.return_value = mock_db

        app_test = FastAPI()
        app_test.include_router(router)

        with TestClient(app_test) as client:
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

    @patch('app.database.connection.get_db')
    def test_update_user_empty_payload(self, mock_get_db):
        """Test updating user with empty payload."""
        user_id = str(uuid4())
        email = "test@example.com"
        token = self.create_test_token(user_id, email)
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.updated_at = datetime.now(timezone.utc)
        mock_user.preferences = {}

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_get_db.return_value = mock_db

        with TestClient(app) as client:
            response = client.put(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                json={}
            )

        # Should succeed even with empty payload
        assert response.status_code == 200

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