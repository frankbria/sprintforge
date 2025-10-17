"""Tests for authentication API endpoints."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID
from jose import jwt
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.auth import NEXTAUTH_SECRET, ALGORITHM, require_auth
from app.models.user import User


@pytest_asyncio.fixture
async def override_auth():
    """Override authentication dependency for testing."""
    def mock_require_auth(user_info: dict):
        return lambda: user_info
    
    yield mock_require_auth
    app.dependency_overrides.clear()


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
    async def test_get_current_user_success(
        self, 
        client: AsyncClient, 
        test_db_session, 
        test_user,
        override_auth
    ):
        """Test successful retrieval of current user."""
        # Mock authentication to return test user's info
        app.dependency_overrides[require_auth] = override_auth({
            "sub": str(test_user.id), 
            "email": test_user.email
        })
        
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
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
    async def test_get_current_user_not_found(
        self, 
        client: AsyncClient, 
        test_db_session,
        override_auth
    ):
        """Test current user retrieval when user not found in database."""
        # Use a valid UUID format but non-existent user
        non_existent_id = str(uuid4())
        
        # Mock authentication to return non-existent user's info
        app.dependency_overrides[require_auth] = override_auth({
            "sub": non_existent_id, 
            "email": "nonexistent@example.com"
        })
        
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(
        self, 
        client: AsyncClient, 
        test_db_session,
        override_auth
    ):
        """Test current user retrieval for inactive user."""
        from app.models.user import User
        
        # Create an inactive user in the database
        inactive_user = User(
            id=uuid4(),
            name="Inactive User",
            email="inactive@example.com",
            subscription_tier="free",
            subscription_status="active",
            is_active=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            preferences={}
        )
        test_db_session.add(inactive_user)
        await test_db_session.commit()
        await test_db_session.refresh(inactive_user)
        
        # Mock authentication to return inactive user's info
        app.dependency_overrides[require_auth] = override_auth({
            "sub": str(inactive_user.id), 
            "email": inactive_user.email
        })
        
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403
        assert "User account is inactive" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_current_user_success(
        self, 
        client: AsyncClient, 
        test_db_session,
        test_user,
        override_auth
    ):
        """Test successful update of current user profile."""
        # Mock authentication to return test user's info
        app.dependency_overrides[require_auth] = override_auth({
            "sub": str(test_user.id), 
            "email": test_user.email
        })
        
        update_data = {
            "name": "Updated Name",
            "preferences": {"theme": "dark", "notifications": True}
        }

        response = await client.put(
            "/api/v1/auth/me",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["preferences"]["theme"] == "dark"
        assert data["preferences"]["notifications"] is True

    @pytest.mark.asyncio
    async def test_update_current_user_partial(
        self, 
        client: AsyncClient, 
        test_db_session,
        test_user,
        override_auth
    ):
        """Test partial update of current user profile."""
        # Mock authentication to return test user's info
        app.dependency_overrides[require_auth] = override_auth({
            "sub": str(test_user.id), 
            "email": test_user.email
        })
        
        update_data = {
            "name": "New Name"
        }

        response = await client.put(
            "/api/v1/auth/me",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_get_session_info_success(
        self, 
        client: AsyncClient, 
        test_db_session,
        test_user,
        override_auth
    ):
        """Test successful retrieval of session information."""
        # Mock authentication to return test user's info with provider
        app.dependency_overrides[require_auth] = override_auth({
            "sub": str(test_user.id), 
            "email": test_user.email,
            "provider": "google",
            "exp": (datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()
        })
        
        response = await client.get("/api/v1/auth/session")

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["id"] == str(test_user.id)
        assert data["user"]["email"] == test_user.email
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
    async def test_update_user_preferences_merge(
        self, 
        client: AsyncClient, 
        test_db_session,
        override_auth
    ):
        """Test that user preferences are properly merged, not replaced."""
        from app.models.user import User
        
        # Create a user with existing preferences
        user_with_prefs = User(
            id=uuid4(),
            name="User With Prefs",
            email="prefs@example.com",
            subscription_tier="free",
            subscription_status="active",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            preferences={"existing": "value", "keep": True}
        )
        test_db_session.add(user_with_prefs)
        await test_db_session.commit()
        await test_db_session.refresh(user_with_prefs)
        
        # Mock authentication to return this user's info
        app.dependency_overrides[require_auth] = override_auth({
            "sub": str(user_with_prefs.id), 
            "email": user_with_prefs.email
        })
        
        update_data = {
            "preferences": {"new": "setting", "existing": "updated"}
        }

        response = await client.put(
            "/api/v1/auth/me",
            json=update_data
        )

        assert response.status_code == 200
        
        # Refresh user to get updated preferences
        await test_db_session.refresh(user_with_prefs)
        
        # Verify preferences were merged
        expected_prefs = {
            "existing": "updated",  # Updated value
            "keep": True,          # Kept existing
            "new": "setting"       # Added new
        }
        assert user_with_prefs.preferences == expected_prefs

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