"""Tests for authentication API endpoints."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID
from jose import jwt
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.auth import NEXTAUTH_SECRET, ALGORITHM
from app.models.user import User


class TestAuthEndpoints:
    """Test authentication API endpoints."""

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

    def create_test_user(self) -> User:
        """Create a test user model."""
        user = User(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            subscription_tier="free",
            subscription_status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            preferences={}
        )
        return user

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful retrieval of current user."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(user.id)
            assert data["email"] == user.email
            assert data["name"] == user.name
            assert data["subscription_tier"] == "free"
            assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self):
        """Test current user retrieval without token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # HTTPBearer returns 403 for missing token

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid_token"}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """Test current user retrieval when user not found in database."""
        token = self.create_test_token("non-existent-user", "test@example.com")

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 404
            assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self):
        """Test current user retrieval for inactive user."""
        user = self.create_test_user()
        user.is_active = False
        token = self.create_test_token(str(user.id), user.email)

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 403
            assert "User account is inactive" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_current_user_success(self):
        """Test successful update of current user profile."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        update_data = {
            "name": "Updated Name",
            "preferences": {"theme": "dark", "notifications": True}
        }

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json=update_data
                )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"

            # Verify database operations were called
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_update_current_user_partial(self):
        """Test partial update of current user profile."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        update_data = {
            "name": "New Name"
        }

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json=update_data
                )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_get_session_info_success(self):
        """Test successful retrieval of session information."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/session",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert "user" in data
            assert data["user"]["id"] == str(user.id)
            assert data["user"]["email"] == user.email
            assert "expires_at" in data
            assert data["provider"] == "google"

    @pytest.mark.asyncio
    async def test_validate_token_success(self):
        """Test successful token validation."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == str(user.id)
        assert data["email"] == user.email
        assert "expires_at" in data

    @pytest.mark.asyncio
    async def test_validate_token_missing(self):
        """Test token validation without token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/validate")

        assert response.status_code == 401
        assert "Invalid or missing token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self):
        """Test token validation with invalid token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/validate",
                headers={"Authorization": "Bearer invalid_token"}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_token_expired(self):
        """Test token validation with expired token."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email, expired=True)

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_session_success(self):
        """Test successful session revocation."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(
                    "/api/v1/auth/session",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 200
            data = response.json()
            assert "Session revoked successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_auth_health_check(self):
        """Test authentication service health check."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_update_user_preferences_merge(self):
        """Test that user preferences are properly merged, not replaced."""
        user = self.create_test_user()
        user.preferences = {"existing": "value", "keep": True}
        token = self.create_test_token(str(user.id), user.email)

        update_data = {
            "preferences": {"new": "setting", "existing": "updated"}
        }

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json=update_data
                )

            assert response.status_code == 200

            # Verify preferences were merged
            expected_prefs = {
                "existing": "updated",  # Updated value
                "keep": True,          # Kept existing
                "new": "setting"       # Added new
            }
            assert user.preferences == expected_prefs

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test proper error handling when database operations fail."""
        user = self.create_test_user()
        token = self.create_test_token(str(user.id), user.email)

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.execute.side_effect = Exception("Database connection failed")
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_user_id_format(self):
        """Test handling of invalid UUID format in token."""
        token = self.create_test_token("invalid-uuid-format", "test@example.com")

        with patch('app.database.connection.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 400
            assert "Invalid user ID" in response.json()["detail"]