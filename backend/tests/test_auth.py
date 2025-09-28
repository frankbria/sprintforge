"""Tests for authentication middleware and JWT validation."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from jose import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import (
    verify_nextauth_jwt,
    get_current_user_from_token,
    get_current_user_optional,
    create_jwt_token,
    verify_user_permissions,
    JWTAuthError,
    NEXTAUTH_SECRET,
    ALGORITHM
)
from app.core.config import settings


class TestJWTValidation:
    """Test JWT token validation functions."""

    def create_test_token(self, payload: dict, expired: bool = False) -> str:
        """Create a test JWT token."""
        if expired:
            exp = datetime.now(timezone.utc) - timedelta(minutes=5)
        else:
            exp = datetime.now(timezone.utc) + timedelta(minutes=30)

        payload.update({
            "exp": exp.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp()
        })

        return jwt.encode(payload, NEXTAUTH_SECRET, algorithm=ALGORITHM)

    @pytest.mark.asyncio
    async def test_verify_valid_jwt(self):
        """Test verification of a valid JWT token."""
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "name": "Test User"
        }
        token = self.create_test_token(payload)

        result = await verify_nextauth_jwt(token)

        assert result["sub"] == "test-user-123"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        assert "exp" in result
        assert "iat" in result

    @pytest.mark.asyncio
    async def test_verify_expired_jwt(self):
        """Test verification of an expired JWT token."""
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        token = self.create_test_token(payload, expired=True)

        with pytest.raises(JWTAuthError) as exc_info:
            await verify_nextauth_jwt(token)

        assert "Token has expired" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_invalid_jwt(self):
        """Test verification of an invalid JWT token."""
        invalid_token = "invalid.jwt.token"

        with pytest.raises(JWTAuthError) as exc_info:
            await verify_nextauth_jwt(invalid_token)

        assert "Invalid token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_jwt_missing_sub(self):
        """Test verification of JWT token missing required 'sub' field."""
        payload = {
            "email": "test@example.com",
            "name": "Test User"
        }
        token = self.create_test_token(payload)

        with pytest.raises(JWTAuthError) as exc_info:
            await verify_nextauth_jwt(token)

        assert "Invalid token: missing user ID" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_from_token_success(self):
        """Test successful user extraction from token."""
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        token = self.create_test_token(payload)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        result = await get_current_user_from_token(credentials)

        assert result["sub"] == "test-user-123"
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_from_token_missing_token(self):
        """Test user extraction with missing token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")

        with pytest.raises(JWTAuthError) as exc_info:
            await get_current_user_from_token(credentials)

        assert "Missing authentication token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_optional_success(self):
        """Test optional user extraction with valid token."""
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        token = self.create_test_token(payload)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        result = await get_current_user_optional(credentials)

        assert result is not None
        assert result["sub"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_token(self):
        """Test optional user extraction with no token."""
        result = await get_current_user_optional(None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_invalid_token(self):
        """Test optional user extraction with invalid token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")

        result = await get_current_user_optional(credentials)

        assert result is None

    def test_create_jwt_token(self):
        """Test JWT token creation."""
        user_data = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "name": "Test User"
        }

        token = create_jwt_token(user_data, expires_delta=30)

        # Verify token can be decoded
        decoded = jwt.decode(token, NEXTAUTH_SECRET, algorithms=[ALGORITHM])
        assert decoded["sub"] == "test-user-123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded
        assert "iat" in decoded

    @pytest.mark.asyncio
    async def test_verify_user_permissions(self):
        """Test user permission verification."""
        user = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        required_permissions = ["read:projects", "write:projects"]

        # For now, this should return True (implementation allows all authenticated users)
        result = await verify_user_permissions(user, required_permissions)

        assert result is True


class TestAuthenticationDependencies:
    """Test authentication dependency functions."""

    @pytest.mark.asyncio
    async def test_require_auth_dependency(self):
        """Test the require_auth dependency."""
        from app.core.auth import require_auth

        user_info = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }

        result = require_auth(user_info)

        assert result == user_info

    @pytest.mark.asyncio
    async def test_optional_auth_dependency_with_user(self):
        """Test the optional_auth dependency with user."""
        from app.core.auth import optional_auth

        user_info = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }

        result = optional_auth(user_info)

        assert result == user_info

    @pytest.mark.asyncio
    async def test_optional_auth_dependency_without_user(self):
        """Test the optional_auth dependency without user."""
        from app.core.auth import optional_auth

        result = optional_auth(None)

        assert result is None


class TestJWTAuthError:
    """Test custom JWT authentication error."""

    def test_jwt_auth_error_default_message(self):
        """Test JWTAuthError with default message."""
        error = JWTAuthError()

        assert error.status_code == 401
        assert error.detail == "Authentication failed"

    def test_jwt_auth_error_custom_message(self):
        """Test JWTAuthError with custom message."""
        custom_message = "Token validation failed"
        error = JWTAuthError(custom_message)

        assert error.status_code == 401
        assert error.detail == custom_message


class TestAuthenticationMiddleware:
    """Test authentication middleware."""

    @pytest.mark.asyncio
    async def test_authentication_middleware_with_valid_token(self):
        """Test middleware with valid authentication token."""
        from app.core.auth import AuthenticationMiddleware

        # Mock app
        mock_app = AsyncMock()
        middleware = AuthenticationMiddleware(mock_app)

        # Create test token
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        token = jwt.encode(
            {**payload, "exp": (datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()},
            NEXTAUTH_SECRET,
            algorithm=ALGORITHM
        )

        # Mock scope with authorization header
        scope = {
            "type": "http",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
            "method": "GET",
            "path": "/api/v1/auth/me"
        }

        receive = AsyncMock()
        send = AsyncMock()

        with patch('app.core.auth.Request') as mock_request_class:
            mock_request = Mock()
            mock_request.headers.get.return_value = f"Bearer {token}"
            mock_request.state = Mock()
            mock_request_class.return_value = mock_request

            await middleware(scope, receive, send)

            # Verify user info was added to request state
            assert hasattr(mock_request.state, 'user')
            assert hasattr(mock_request.state, 'user_id')
            assert hasattr(mock_request.state, 'user_email')
            assert mock_request.state.user_id == "test-user-123"
            assert mock_request.state.user_email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authentication_middleware_with_invalid_token(self):
        """Test middleware with invalid authentication token."""
        from app.core.auth import AuthenticationMiddleware

        # Mock app
        mock_app = AsyncMock()
        middleware = AuthenticationMiddleware(mock_app)

        # Mock scope with invalid authorization header
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer invalid_token")],
            "method": "GET",
            "path": "/api/v1/auth/me"
        }

        receive = AsyncMock()
        send = AsyncMock()

        with patch('app.core.auth.Request') as mock_request_class:
            mock_request = Mock()
            mock_request.headers.get.return_value = "Bearer invalid_token"
            mock_request.state = Mock()
            mock_request_class.return_value = mock_request

            await middleware(scope, receive, send)

            # Verify no user info was added (invalid token should be ignored)
            assert not hasattr(mock_request.state, 'user')

    @pytest.mark.asyncio
    async def test_authentication_middleware_without_token(self):
        """Test middleware without authentication token."""
        from app.core.auth import AuthenticationMiddleware

        # Mock app
        mock_app = AsyncMock()
        middleware = AuthenticationMiddleware(mock_app)

        # Mock scope without authorization header
        scope = {
            "type": "http",
            "headers": [],
            "method": "GET",
            "path": "/api/v1/projects"
        }

        receive = AsyncMock()
        send = AsyncMock()

        with patch('app.core.auth.Request') as mock_request_class:
            mock_request = Mock()
            mock_request.headers.get.return_value = None
            mock_request.state = Mock()
            mock_request_class.return_value = mock_request

            await middleware(scope, receive, send)

            # Verify no user info was added
            assert not hasattr(mock_request.state, 'user')

    @pytest.mark.asyncio
    async def test_authentication_middleware_non_http_scope(self):
        """Test middleware with non-HTTP scope."""
        from app.core.auth import AuthenticationMiddleware

        # Mock app
        mock_app = AsyncMock()
        middleware = AuthenticationMiddleware(mock_app)

        # Mock non-HTTP scope (e.g., WebSocket)
        scope = {
            "type": "websocket"
        }

        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # Verify app was called directly (middleware should pass through)
        mock_app.assert_called_once_with(scope, receive, send)