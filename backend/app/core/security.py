"""
Security utilities and middleware for SprintForge.
"""

import time
from typing import Dict, Optional
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import Response
import structlog

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with per-endpoint and per-user limits."""

    def __init__(self, app, default_requests: int = 100, default_window: int = 60):
        super().__init__(app)
        self.default_requests = default_requests
        self.default_window = default_window

        # Rate limit storage: {identifier: deque of timestamps}
        self.requests: Dict[str, deque] = defaultdict(deque)

        # Per-endpoint rate limits
        self.endpoint_limits = {
            "/api/v1/auth/login": {"requests": 5, "window": 60},  # 5 login attempts per minute
            "/api/v1/auth/register": {"requests": 3, "window": 300},  # 3 registrations per 5 minutes
            "/api/v1/projects/generate": {"requests": 10, "window": 60},  # 10 Excel generations per minute
            "/health": {"requests": 200, "window": 60},  # High limit for health checks
        }

    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _get_rate_limit(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for a path."""
        for endpoint_path, limits in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return limits

        return {"requests": self.default_requests, "window": self.default_window}

    def _is_rate_limited(self, identifier: str, limits: Dict[str, int]) -> bool:
        """Check if identifier is rate limited."""
        now = time.time()
        window_start = now - limits["window"]

        # Clean old requests outside the window
        request_times = self.requests[identifier]
        while request_times and request_times[0] < window_start:
            request_times.popleft()

        # Check if we've exceeded the limit
        if len(request_times) >= limits["requests"]:
            return True

        # Add current request
        request_times.append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        """Process rate limiting for each request."""
        path = request.url.path
        identifier = self._get_client_identifier(request)
        limits = self._get_rate_limit(path)

        # Check rate limit
        if self._is_rate_limited(identifier, limits):
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                path=path,
                limits=limits
            )

            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": str(limits["window"]),
                    "X-RateLimit-Limit": str(limits["requests"]),
                    "X-RateLimit-Window": str(limits["window"]),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = max(0, limits["requests"] - len(self.requests[identifier]))
        response.headers["X-RateLimit-Limit"] = str(limits["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(limits["window"])

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

        # Only add HSTS in production with HTTPS
        if request.url.scheme == "https":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Add Content Security Policy for HTML responses
        if response.headers.get("content-type", "").startswith("text/html"):
            security_headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )

        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value

        return response


def validate_input_length(value: str, field_name: str, max_length: int = 1000) -> str:
    """Validate input string length to prevent DoS attacks."""
    if len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} exceeds maximum length of {max_length} characters"
        )
    return value


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    import re
    import os.path

    # Remove path separators and dangerous characters
    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)

    # Prevent hidden files and relative paths
    safe_filename = safe_filename.lstrip('.')

    # Ensure it's not empty
    if not safe_filename:
        safe_filename = "unnamed_file"

    # Limit length
    safe_filename = safe_filename[:255]

    return safe_filename


def get_client_ip(request: Request) -> str:
    """Get client IP address from request, handling proxies."""
    # Check X-Forwarded-For header (proxy)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP (original client)
        client_ip = forwarded_for.split(",")[0].strip()
        return client_ip

    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    # Fall back to direct connection
    return request.client.host if request.client else "unknown"


def is_safe_redirect_url(url: str, allowed_hosts: list) -> bool:
    """Check if a redirect URL is safe (prevents open redirect attacks)."""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # Relative URLs are safe
        if not parsed.netloc:
            return True

        # Check if host is in allowed list
        return parsed.netloc in allowed_hosts

    except Exception:
        return False


class InputValidationError(HTTPException):
    """Custom exception for input validation errors."""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


def validate_json_size(data: dict, max_size: int = 1024 * 1024) -> dict:
    """Validate JSON data size to prevent memory exhaustion."""
    import json

    # Serialize to estimate size
    json_str = json.dumps(data)
    size = len(json_str.encode('utf-8'))

    if size > max_size:
        raise InputValidationError(
            f"JSON data size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        )

    return data


def validate_project_config(config: dict) -> dict:
    """Validate project configuration structure and values."""
    # Required fields
    required_fields = ["sprint_pattern", "sprint_duration_weeks", "working_days"]
    for field in required_fields:
        if field not in config:
            raise InputValidationError(f"Missing required field: {field}")

    # Validate sprint duration
    sprint_duration = config.get("sprint_duration_weeks", 0)
    if not isinstance(sprint_duration, int) or not (1 <= sprint_duration <= 8):
        raise InputValidationError("Sprint duration must be between 1 and 8 weeks")

    # Validate working days
    working_days = config.get("working_days", [])
    if not isinstance(working_days, list) or not all(isinstance(day, int) and 1 <= day <= 7 for day in working_days):
        raise InputValidationError("Working days must be a list of integers between 1 and 7")

    # Validate sprint pattern
    sprint_pattern = config.get("sprint_pattern", "")
    valid_patterns = ["YY.Q.#", "PI-N.Sprint-M", "YYYY.MM.#", "Custom"]
    if sprint_pattern not in valid_patterns:
        raise InputValidationError(f"Invalid sprint pattern. Must be one of: {valid_patterns}")

    # Validate JSON size
    validate_json_size(config, max_size=512 * 1024)  # 512KB limit for project config

    return config