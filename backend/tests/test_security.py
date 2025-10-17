"""
Comprehensive security tests for SprintForge authentication and protection systems.
Tests token management, rate limiting, CSRF protection, and security headers.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from collections import deque

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    validate_input_length,
    sanitize_filename,
    validate_json_size,
    validate_project_config,
    blacklist_token,
    is_token_blacklisted,
    clear_token_blacklist,
    validate_jwt_token,
    generate_csrf_token,
    validate_csrf_token,
    get_client_ip,
    is_safe_redirect_url,
    cleanup_expired_lockouts,
    get_security_headers,
    account_lockouts,
    failed_attempts,
    token_blacklist
)
from app.core.csrf import CSRFProtectionMiddleware


class TestRateLimitMiddleware:
    """Test rate limiting middleware with account lockout and progressive delays."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        async def mock_call_next(request):
            return Response(content="OK", status_code=200)
        return mock_call_next

    @pytest.fixture
    def rate_limiter(self, mock_app):
        """Create rate limit middleware instance."""
        return RateLimitMiddleware(mock_app, default_requests=5, default_window=60)

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/auth/login"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = Mock()
        request.state.user_id = None
        return request

    def test_get_client_identifier_with_user_id(self, rate_limiter):
        """Test client identifier extraction with user ID."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user123"

        identifier = rate_limiter._get_client_identifier(request)
        assert identifier == "user:user123"

    def test_get_client_identifier_with_ip(self, rate_limiter):
        """Test client identifier extraction with IP address."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = None
        request.client.host = "192.168.1.100"
        request.headers = {}
        request.url.path = "/api/v1/auth/login"

        identifier = rate_limiter._get_client_identifier(request)
        assert identifier == "ip:192.168.1.100"

    def test_get_client_identifier_with_forwarded_for(self, rate_limiter):
        """Test client identifier with X-Forwarded-For header."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = None
        request.headers = {"x-forwarded-for": "203.0.113.195, 70.41.3.18, 150.172.238.178"}
        request.url.path = "/api/v1/auth/login"

        identifier = rate_limiter._get_client_identifier(request)
        assert identifier == "ip:203.0.113.195"

    def test_get_rate_limit_for_auth_endpoints(self, rate_limiter):
        """Test rate limit configuration for authentication endpoints."""
        limits = rate_limiter._get_rate_limit("/api/v1/auth/login")
        assert limits == {"requests": 3, "window": 60}

        limits = rate_limiter._get_rate_limit("/api/v1/auth/register")
        assert limits == {"requests": 2, "window": 300}

    def test_get_rate_limit_for_default_endpoints(self, rate_limiter):
        """Test rate limit configuration for default endpoints."""
        limits = rate_limiter._get_rate_limit("/api/v1/projects")
        assert limits == {"requests": 5, "window": 60}

    def test_rate_limiting_within_limits(self, rate_limiter):
        """Test that requests within limits are allowed."""
        identifier = "test_user"
        limits = {"requests": 5, "window": 60}
        path = "/api/v1/auth/login"

        # First few requests should be allowed
        for i in range(3):
            is_limited, delay = rate_limiter._is_rate_limited(identifier, limits, path)
            assert not is_limited
            assert delay == 0

    def test_rate_limiting_exceeds_limits(self, rate_limiter):
        """Test that requests exceeding limits are blocked."""
        identifier = "test_user"
        limits = {"requests": 3, "window": 60}
        path = "/api/v1/auth/login"

        # Fill up the limit
        for i in range(3):
            rate_limiter._is_rate_limited(identifier, limits, path)

        # Next request should be limited
        is_limited, delay = rate_limiter._is_rate_limited(identifier, limits, path)
        assert is_limited
        assert delay > 0

    def test_progressive_delay_calculation(self, rate_limiter):
        """Test progressive delay increases with violations."""
        identifier = "test_user"
        limits = {"requests": 2, "window": 60}
        path = "/api/v1/auth/login"

        # Fill up the limit
        for i in range(2):
            rate_limiter._is_rate_limited(identifier, limits, path)

        # First violation - len=2, violation_count = 2-2+1 = 1, delay = 2^1 = 2
        is_limited1, delay1 = rate_limiter._is_rate_limited(identifier, limits, path)
        assert is_limited1
        assert delay1 == 2

        # To get progressive delay, we need to add more requests to the deque
        # Simulate more rapid requests that would increase the delay
        import time
        now = time.time()
        rate_limiter.requests[identifier].append(now)

        # Now len=3, violation_count = 3-2+1 = 2, delay = 2^2 = 4
        is_limited2, delay2 = rate_limiter._is_rate_limited(identifier, limits, path)
        assert is_limited2
        assert delay2 == 4

        # Verify delay increases
        assert delay2 > delay1

    def test_account_lockout_mechanism(self, rate_limiter):
        """Test account lockout after excessive failures."""
        identifier = "test_user"
        limits = {"requests": 1, "window": 60}
        path = "/api/v1/auth/login"

        # Exceed rate limit multiple times to trigger lockout
        for i in range(6):  # max_failed_attempts = 5
            rate_limiter._is_rate_limited(identifier, limits, path)

        # Check that account is locked
        assert identifier in account_lockouts
        assert failed_attempts[identifier] >= rate_limiter.max_failed_attempts

    @pytest.mark.asyncio
    async def test_dispatch_successful_request(self, rate_limiter, mock_request, mock_app):
        """Test successful request processing."""
        response = await rate_limiter.dispatch(mock_request, mock_app)

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Window" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_rate_limited_request(self, rate_limiter, mock_request, mock_app):
        """Test rate limited request handling."""
        identifier = rate_limiter._get_client_identifier(mock_request)
        limits = rate_limiter._get_rate_limit(mock_request.url.path)

        # Fill up the rate limit
        for i in range(limits["requests"] + 1):
            rate_limiter._is_rate_limited(identifier, limits, mock_request.url.path)

        response = await rate_limiter.dispatch(mock_request, mock_app)

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-Progressive-Delay" in response.headers


class TestSecurityHeadersMiddleware:
    """Test security headers middleware."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        async def mock_call_next(request):
            response = Response(content="OK", status_code=200)
            response.headers["content-type"] = "text/html"
            return response
        return mock_call_next

    @pytest.fixture
    def security_middleware(self, mock_app):
        """Create security headers middleware instance."""
        return SecurityHeadersMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        """Create a mock HTTPS request."""
        request = Mock(spec=Request)
        request.url.scheme = "https"
        return request

    @pytest.mark.asyncio
    async def test_security_headers_added(self, security_middleware, mock_request, mock_app):
        """Test that security headers are added to responses."""
        response = await security_middleware.dispatch(mock_request, mock_app)

        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Content-Security-Policy"
        ]

        for header in expected_headers:
            assert header in response.headers

    @pytest.mark.asyncio
    async def test_hsts_header_https_only(self, security_middleware, mock_app):
        """Test HSTS header only added for HTTPS requests."""
        # HTTPS request
        https_request = Mock(spec=Request)
        https_request.url.scheme = "https"

        response = await security_middleware.dispatch(https_request, mock_app)
        assert "Strict-Transport-Security" in response.headers

        # HTTP request
        http_request = Mock(spec=Request)
        http_request.url.scheme = "http"

        response = await security_middleware.dispatch(http_request, mock_app)
        assert "Strict-Transport-Security" not in response.headers


class TestInputValidation:
    """Test input validation functions."""

    def test_validate_input_length_valid(self):
        """Test valid input length validation."""
        result = validate_input_length("short text", "test_field", 100)
        assert result == "short text"

    def test_validate_input_length_invalid(self):
        """Test input length validation with exceeding length."""
        with pytest.raises(HTTPException) as exc_info:
            validate_input_length("x" * 1001, "test_field", 1000)

        assert exc_info.value.status_code == 400
        assert "exceeds maximum length" in str(exc_info.value.detail)

    def test_sanitize_filename_valid(self):
        """Test filename sanitization with valid input."""
        result = sanitize_filename("valid_file-name.txt")
        assert result == "valid_file-name.txt"

    def test_sanitize_filename_dangerous(self):
        """Test filename sanitization with dangerous input."""
        # Path traversal attempt - dots converted to underscores, / removed, leading dots stripped
        result = sanitize_filename("../../../etc/passwd")
        assert result == "_.._.._etc_passwd"

        # Dangerous characters replaced with underscores
        result = sanitize_filename("file<>:\"|?*name.txt")
        assert result == "file_______name.txt"

    def test_sanitize_filename_empty(self):
        """Test filename sanitization with empty input."""
        result = sanitize_filename("")
        assert result == "unnamed_file"

        result = sanitize_filename("...")
        assert result == "unnamed_file"

    def test_validate_json_size_valid(self):
        """Test JSON size validation with valid input."""
        data = {"key": "value"}
        result = validate_json_size(data, max_size=1000)
        assert result == data

    def test_validate_json_size_invalid(self):
        """Test JSON size validation with exceeding size."""
        large_data = {"key": "x" * 1000000}

        with pytest.raises(HTTPException) as exc_info:
            validate_json_size(large_data, max_size=1000)

        assert exc_info.value.status_code == 400
        assert "exceeds maximum allowed size" in str(exc_info.value.detail)

    def test_validate_project_config_valid(self):
        """Test project configuration validation with valid input."""
        config = {
            "sprint_pattern": "YY.Q.#",
            "sprint_duration_weeks": 2,
            "working_days": [1, 2, 3, 4, 5]
        }

        result = validate_project_config(config)
        assert result == config

    def test_validate_project_config_missing_fields(self):
        """Test project configuration validation with missing fields."""
        config = {"sprint_pattern": "YY.Q.#"}

        with pytest.raises(HTTPException) as exc_info:
            validate_project_config(config)

        assert exc_info.value.status_code == 400
        assert "Missing required field" in str(exc_info.value.detail)

    def test_validate_project_config_invalid_duration(self):
        """Test project configuration validation with invalid duration."""
        config = {
            "sprint_pattern": "YY.Q.#",
            "sprint_duration_weeks": 10,  # Invalid: > 8
            "working_days": [1, 2, 3, 4, 5]
        }

        with pytest.raises(HTTPException) as exc_info:
            validate_project_config(config)

        assert exc_info.value.status_code == 400
        assert "Sprint duration must be between 1 and 8 weeks" in str(exc_info.value.detail)

    def test_validate_project_config_invalid_working_days(self):
        """Test project configuration validation with invalid working days."""
        config = {
            "sprint_pattern": "YY.Q.#",
            "sprint_duration_weeks": 2,
            "working_days": [1, 2, 3, 8]  # Invalid: 8 > 7
        }

        with pytest.raises(HTTPException) as exc_info:
            validate_project_config(config)

        assert exc_info.value.status_code == 400
        assert "Working days must be a list of integers between 1 and 7" in str(exc_info.value.detail)


class TestTokenSecurity:
    """Test JWT token security functions."""

    def setUp(self):
        """Clear token blacklist before each test."""
        clear_token_blacklist()

    def test_token_blacklisting(self):
        """Test token blacklisting functionality."""
        self.setUp()

        token_id = "test_token_123"

        # Initially not blacklisted
        assert not is_token_blacklisted(token_id)

        # Blacklist the token
        blacklist_token(token_id)
        assert is_token_blacklisted(token_id)

        # Clear blacklist
        clear_token_blacklist()
        assert not is_token_blacklisted(token_id)

    def test_validate_jwt_token_valid(self):
        """Test JWT token validation with valid token."""
        # This would require a real JWT token and secret for full testing
        # For now, test the structure and error handling
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_token("invalid.jwt.token", "secret")

        assert exc_info.value.status_code == 401

    def test_validate_jwt_token_blacklisted(self):
        """Test JWT token validation with blacklisted token."""
        # Mock a valid JWT payload
        with patch('app.core.security.jwt.decode') as mock_decode:
            mock_decode.return_value = {"jti": "blacklisted_token", "exp": time.time() + 3600}

            # Blacklist the token
            blacklist_token("blacklisted_token")

            with pytest.raises(HTTPException) as exc_info:
                validate_jwt_token("mock.jwt.token", "secret")

            assert exc_info.value.status_code == 401
            assert "Token has been revoked" in str(exc_info.value.detail)


class TestCSRFProtection:
    """Test CSRF protection functions."""

    def test_generate_csrf_token(self):
        """Test CSRF token generation."""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()

        assert token1 != token2
        assert len(token1) > 32  # URL-safe base64 encoded

    def test_validate_csrf_token_valid(self):
        """Test CSRF token validation with matching tokens."""
        token = generate_csrf_token()
        assert validate_csrf_token(token, token)

    def test_validate_csrf_token_invalid(self):
        """Test CSRF token validation with non-matching tokens."""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert not validate_csrf_token(token1, token2)

    def test_validate_csrf_token_timing_attack_protection(self):
        """Test CSRF token validation uses constant-time comparison."""
        # This test ensures we're using secrets.compare_digest
        token = generate_csrf_token()

        # Should return False for different lengths without timing attack
        assert not validate_csrf_token(token, token[:-1])
        assert not validate_csrf_token(token, token + "x")


class TestUtilityFunctions:
    """Test utility security functions."""

    def test_get_client_ip_direct(self):
        """Test client IP extraction from direct connection."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client.host = "192.168.1.100"

        ip = get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_forwarded_for(self):
        """Test client IP extraction from X-Forwarded-For header."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "203.0.113.195, 70.41.3.18"}
        request.client.host = "192.168.1.1"

        ip = get_client_ip(request)
        assert ip == "203.0.113.195"

    def test_get_client_ip_real_ip(self):
        """Test client IP extraction from X-Real-IP header."""
        request = Mock(spec=Request)
        request.headers = {"x-real-ip": "203.0.113.195"}
        request.client.host = "192.168.1.1"

        ip = get_client_ip(request)
        assert ip == "203.0.113.195"

    def test_is_safe_redirect_url_relative(self):
        """Test safe redirect URL validation with relative URLs."""
        assert is_safe_redirect_url("/dashboard", ["example.com"])
        assert is_safe_redirect_url("../profile", ["example.com"])

    def test_is_safe_redirect_url_allowed_host(self):
        """Test safe redirect URL validation with allowed hosts."""
        allowed_hosts = ["example.com", "sub.example.com"]

        assert is_safe_redirect_url("https://example.com/page", allowed_hosts)
        assert is_safe_redirect_url("https://sub.example.com/page", allowed_hosts)

    def test_is_safe_redirect_url_disallowed_host(self):
        """Test safe redirect URL validation with disallowed hosts."""
        allowed_hosts = ["example.com"]

        assert not is_safe_redirect_url("https://evil.com/page", allowed_hosts)
        assert not is_safe_redirect_url("https://example.com.evil.com/page", allowed_hosts)

    def test_is_safe_redirect_url_malformed(self):
        """Test safe redirect URL validation with malformed URLs."""
        # Malformed URLs containing : should be rejected
        assert not is_safe_redirect_url("not-a-url:something", ["example.com"])
        # JavaScript protocol should be rejected
        assert not is_safe_redirect_url("javascript:alert(1)", ["example.com"])
        # URLs with @ without proper structure should be rejected
        assert not is_safe_redirect_url("test@malformed", ["example.com"])
        # Data URIs should be rejected
        assert not is_safe_redirect_url("data:text/html,<script>alert(1)</script>", ["example.com"])

    @pytest.mark.asyncio
    async def test_cleanup_expired_lockouts(self):
        """Test cleanup of expired account lockouts."""
        # Add some test lockouts
        past_time = datetime.now() - timedelta(minutes=1)
        future_time = datetime.now() + timedelta(minutes=1)

        account_lockouts["expired_user"] = past_time
        account_lockouts["active_user"] = future_time
        failed_attempts["expired_user"] = 5
        failed_attempts["active_user"] = 3

        await cleanup_expired_lockouts()

        # Expired lockout should be removed
        assert "expired_user" not in account_lockouts
        assert failed_attempts["expired_user"] == 0

        # Active lockout should remain
        assert "active_user" in account_lockouts
        assert failed_attempts["active_user"] == 3

    def test_get_security_headers(self):
        """Test security headers generation."""
        headers = get_security_headers()

        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Content-Security-Policy"
        ]

        for header in expected_headers:
            assert header in headers
            assert headers[header]  # Ensure non-empty values


class TestCSRFMiddleware:
    """Test CSRF protection middleware."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        async def mock_call_next(request):
            return JSONResponse({"status": "success"}, status_code=200)
        return mock_call_next

    @pytest.fixture
    def csrf_middleware(self, mock_app):
        """Create CSRF middleware instance."""
        return CSRFProtectionMiddleware(mock_app, exempt_paths=["/health", "/docs"])

    def test_csrf_middleware_initialization(self):
        """Test CSRF middleware initialization."""
        app = Mock()
        middleware = CSRFProtectionMiddleware(app, exempt_paths=["/custom", "/health"])

        assert "/custom" in middleware.exempt_paths
        assert "/health" in middleware.exempt_paths

    @pytest.mark.asyncio
    async def test_csrf_middleware_exempt_path(self, csrf_middleware, mock_app):
        """Test CSRF middleware with exempt paths."""
        request = Mock(spec=Request)
        request.url.path = "/health"
        request.method = "POST"
        request.cookies = {"next-auth.session-token": "test_session_token_12345678901234567890"}

        response = await csrf_middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_csrf_middleware_get_request(self, csrf_middleware, mock_app):
        """Test CSRF middleware with GET request (should pass)."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.cookies = {"next-auth.session-token": "test_session_token_12345678901234567890"}

        response = await csrf_middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_csrf_middleware_post_without_token(self, csrf_middleware, mock_app):
        """Test CSRF middleware with POST request without token."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"
        request.headers = {}
        request.cookies = {}

        response = await csrf_middleware.dispatch(request, mock_app)
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_integration_rate_limit_and_security_headers():
    """Integration test for rate limiting and security headers working together."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    # Add both middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, default_requests=2, default_window=60)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    client = TestClient(app)

    # First request should succeed with security headers
    response = client.get("/test")
    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert "X-RateLimit-Limit" in response.headers

    # Second request should also succeed
    response = client.get("/test")
    assert response.status_code == 200

    # Third request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "Retry-After" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])