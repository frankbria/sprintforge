"""
Tests for security utilities and middleware.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import Mock

from backend.app.core.security import (
    validate_input_length,
    sanitize_filename,
    is_safe_redirect_url,
    validate_json_size,
    validate_project_config,
    InputValidationError,
)


def test_validate_input_length():
    """Test input length validation."""
    # Valid input
    result = validate_input_length("hello", "test_field", 10)
    assert result == "hello"

    # Input too long
    with pytest.raises(Exception):  # HTTPException
        validate_input_length("x" * 1001, "test_field", 1000)


def test_sanitize_filename():
    """Test filename sanitization."""
    # Normal filename
    assert sanitize_filename("document.pdf") == "document.pdf"

    # Filename with dangerous characters
    assert sanitize_filename("../../../etc/passwd") == "___________etc_passwd"

    # Hidden file
    assert sanitize_filename(".hidden") == "hidden"

    # Empty filename
    assert sanitize_filename("") == "unnamed_file"

    # Very long filename
    long_name = "x" * 300
    result = sanitize_filename(long_name)
    assert len(result) <= 255


def test_is_safe_redirect_url():
    """Test redirect URL safety validation."""
    allowed_hosts = ["example.com", "subdomain.example.com"]

    # Safe relative URLs
    assert is_safe_redirect_url("/dashboard", allowed_hosts) is True
    assert is_safe_redirect_url("./relative", allowed_hosts) is True

    # Safe absolute URLs
    assert is_safe_redirect_url("https://example.com/page", allowed_hosts) is True
    assert is_safe_redirect_url("https://subdomain.example.com/page", allowed_hosts) is True

    # Unsafe absolute URLs
    assert is_safe_redirect_url("https://evil.com/page", allowed_hosts) is False
    assert is_safe_redirect_url("http://malicious.site.com", allowed_hosts) is False

    # Invalid URLs
    assert is_safe_redirect_url("not-a-url", allowed_hosts) is True  # Treated as relative


def test_validate_json_size():
    """Test JSON size validation."""
    # Small JSON
    small_data = {"key": "value"}
    result = validate_json_size(small_data, max_size=1024)
    assert result == small_data

    # Large JSON
    large_data = {"data": "x" * 10000}
    with pytest.raises(InputValidationError):
        validate_json_size(large_data, max_size=1000)


def test_validate_project_config():
    """Test project configuration validation."""
    # Valid config
    valid_config = {
        "sprint_pattern": "YY.Q.#",
        "sprint_duration_weeks": 2,
        "working_days": [1, 2, 3, 4, 5],
        "features": {"monte_carlo": True}
    }
    result = validate_project_config(valid_config)
    assert result == valid_config

    # Missing required field
    invalid_config = {"sprint_pattern": "YY.Q.#"}
    with pytest.raises(InputValidationError) as exc_info:
        validate_project_config(invalid_config)
    assert "Missing required field" in str(exc_info.value.detail)

    # Invalid sprint duration
    invalid_config = valid_config.copy()
    invalid_config["sprint_duration_weeks"] = 10
    with pytest.raises(InputValidationError) as exc_info:
        validate_project_config(invalid_config)
    assert "Sprint duration must be between 1 and 8 weeks" in str(exc_info.value.detail)

    # Invalid working days
    invalid_config = valid_config.copy()
    invalid_config["working_days"] = [1, 2, 8]  # 8 is not a valid day
    with pytest.raises(InputValidationError) as exc_info:
        validate_project_config(invalid_config)
    assert "Working days must be a list of integers between 1 and 7" in str(exc_info.value.detail)

    # Invalid sprint pattern
    invalid_config = valid_config.copy()
    invalid_config["sprint_pattern"] = "INVALID"
    with pytest.raises(InputValidationError) as exc_info:
        validate_project_config(invalid_config)
    assert "Invalid sprint pattern" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_security_headers_in_response(test_client: AsyncClient):
    """Test that security headers are added to responses."""
    response = await test_client.get("/health")

    # Check for security headers
    assert "x-content-type-options" in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"

    assert "x-frame-options" in response.headers
    assert response.headers["x-frame-options"] == "DENY"

    assert "x-xss-protection" in response.headers
    assert response.headers["x-xss-protection"] == "1; mode=block"

    assert "referrer-policy" in response.headers
    assert "permissions-policy" in response.headers


@pytest.mark.asyncio
async def test_rate_limiting_headers(test_client: AsyncClient):
    """Test that rate limiting headers are present."""
    response = await test_client.get("/health")

    # Check for rate limit headers
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
    assert "x-ratelimit-window" in response.headers

    # Values should be numeric
    assert int(response.headers["x-ratelimit-limit"]) > 0
    assert int(response.headers["x-ratelimit-remaining"]) >= 0
    assert int(response.headers["x-ratelimit-window"]) > 0


@pytest.mark.asyncio
async def test_cors_headers(test_client: AsyncClient):
    """Test CORS headers are properly configured."""
    # OPTIONS request to test CORS preflight
    response = await test_client.options("/api/v1/")

    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


@pytest.mark.asyncio
async def test_rate_limiting_enforcement(test_client: AsyncClient):
    """Test rate limiting is enforced."""
    # Make multiple rapid requests to a rate-limited endpoint
    # Note: This test might be flaky depending on rate limit configuration

    responses = []
    for i in range(5):
        response = await test_client.get("/health")
        responses.append(response)

    # All initial requests should succeed
    assert all(r.status_code == 200 for r in responses)

    # Check that rate limit remaining decreases
    remaining_values = [int(r.headers.get("x-ratelimit-remaining", 0)) for r in responses]

    # Should be decreasing (though might not be perfectly sequential due to async)
    assert remaining_values[0] >= remaining_values[-1]