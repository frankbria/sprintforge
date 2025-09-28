"""
CSRF Protection utilities for SprintForge API.
"""

import secrets
import time
from typing import Optional
from fastapi import HTTPException, Request
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import Response
import structlog

logger = structlog.get_logger(__name__)

# CSRF token storage (use Redis in production)
csrf_tokens = {}


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for state-changing operations."""

    def __init__(self, app, exempt_paths: list = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        # Methods that require CSRF protection
        self.protected_methods = {"POST", "PUT", "PATCH", "DELETE"}

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    def _generate_csrf_token(self, session_id: str) -> str:
        """Generate a new CSRF token for a session."""
        token = secrets.token_urlsafe(32)
        csrf_tokens[session_id] = {
            "token": token,
            "created": time.time()
        }
        return token

    def _validate_csrf_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token for a session."""
        if session_id not in csrf_tokens:
            return False

        stored_data = csrf_tokens[session_id]
        stored_token = stored_data["token"]
        created_time = stored_data["created"]

        # Check token age (max 1 hour)
        if time.time() - created_time > 3600:
            del csrf_tokens[session_id]
            return False

        # Use constant-time comparison
        return secrets.compare_digest(token, stored_token)

    def _get_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request."""
        # Try to get from NextAuth session cookie
        session_cookie = request.cookies.get("next-auth.session-token")
        if session_cookie:
            return session_cookie[:32]  # Use first 32 chars as session ID

        # Fall back to user ID from request state
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        return None

    async def dispatch(self, request: Request, call_next):
        """Process CSRF protection for each request."""
        path = request.url.path
        method = request.method

        # Skip non-protected methods and exempt paths
        if method not in self.protected_methods or self._is_exempt(path):
            response = await call_next(request)
            
            # Always add CSRF token to response headers for client to use
            session_id = self._get_session_id(request)
            if session_id:
                csrf_token = self._generate_csrf_token(session_id)
                response.headers["X-CSRF-Token"] = csrf_token
            
            return response

        # Check for CSRF token in headers
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            logger.warning("Missing CSRF token", path=path, method=method)
            return Response(
                content='{"detail": "CSRF token missing"}',
                status_code=403,
                headers={"Content-Type": "application/json"}
            )

        # Validate CSRF token
        session_id = self._get_session_id(request)
        if not session_id or not self._validate_csrf_token(session_id, csrf_token):
            logger.warning("Invalid CSRF token", path=path, method=method, session_id=session_id)
            return Response(
                content='{"detail": "CSRF token invalid"}',
                status_code=403,
                headers={"Content-Type": "application/json"}
            )

        # Process request
        response = await call_next(request)

        # Generate new CSRF token for next request
        new_csrf_token = self._generate_csrf_token(session_id)
        response.headers["X-CSRF-Token"] = new_csrf_token

        return response


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, expected: str) -> bool:
    """Validate CSRF token using constant-time comparison."""
    return secrets.compare_digest(token, expected)


def cleanup_expired_csrf_tokens():
    """Clean up expired CSRF tokens (should be called periodically)."""
    current_time = time.time()
    expired_sessions = [
        session_id for session_id, data in csrf_tokens.items()
        if current_time - data["created"] > 3600
    ]
    
    for session_id in expired_sessions:
        del csrf_tokens[session_id]
    
    if expired_sessions:
        logger.info("Cleaned up expired CSRF tokens", count=len(expired_sessions))