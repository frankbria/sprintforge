"""Authentication utilities and JWT token validation for NextAuth.js integration."""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Custom HTTPBearer that returns 401 instead of 403 for missing auth
class HTTPBearerWith401(HTTPBearer):
    """Custom HTTPBearer that returns 401 Unauthorized instead of 403 Forbidden."""

    async def __call__(self, request: Request):
        """Override to return 401 when authentication is missing."""
        try:
            return await super().__call__(request)
        except HTTPException as e:
            if e.status_code == 403:
                # Convert 403 to 401 for missing/invalid authentication
                raise JWTAuthError("Authentication required")
            raise

# Security scheme for API documentation
security = HTTPBearerWith401()

# NextAuth.js JWT configuration
NEXTAUTH_SECRET = settings.secret_key
ALGORITHM = settings.algorithm


class JWTAuthError(HTTPException):
    """Custom exception for JWT authentication errors."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)


async def verify_nextauth_jwt(token: str) -> Dict[str, Any]:
    """
    Verify a NextAuth.js JWT token and extract user information.

    Args:
        token: The JWT token string

    Returns:
        Dict containing decoded token payload

    Raises:
        JWTAuthError: If token is invalid or expired
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token,
            NEXTAUTH_SECRET,
            algorithms=[ALGORITHM]
        )

        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise JWTAuthError("Token has expired")

        # Validate required fields
        if not payload.get("sub"):
            raise JWTAuthError("Invalid token: missing user ID")

        logger.info(
            "JWT token validated successfully",
            user_id=payload.get("sub"),
            email=payload.get("email")
        )

        return payload

    except JWTError as e:
        error_str = str(e)
        logger.warning("JWT validation failed", error=error_str)
        # Check for specific error types
        if "expired" in error_str.lower():
            raise JWTAuthError("Token has expired")
        raise JWTAuthError("Invalid token")
    except JWTAuthError:
        # Re-raise JWTAuthError as-is (from missing sub check)
        raise
    except Exception as e:
        logger.error("Unexpected error during JWT validation", error=str(e))
        raise JWTAuthError("Authentication error")


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Extract and validate user information from JWT token in Authorization header.

    Args:
        credentials: HTTP authorization credentials from request header

    Returns:
        Dict containing user information from token

    Raises:
        JWTAuthError: If authentication fails
    """
    if not credentials or not credentials.credentials:
        raise JWTAuthError("Missing authentication token")

    token = credentials.credentials
    user_info = await verify_nextauth_jwt(token)

    return user_info


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Optionally extract user information from JWT token. Returns None if no token provided.

    Args:
        credentials: Optional HTTP authorization credentials

    Returns:
        Dict containing user information or None if no token
    """
    if not credentials or not credentials.credentials:
        return None

    try:
        return await verify_nextauth_jwt(credentials.credentials)
    except JWTAuthError:
        return None


def require_auth(user: Dict[str, Any] = Depends(get_current_user_from_token)) -> Dict[str, Any]:
    """
    Dependency that requires authentication. Use this for protected endpoints.

    Args:
        user: User information from JWT token

    Returns:
        User information dict
    """
    return user


def optional_auth(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)) -> Optional[Dict[str, Any]]:
    """
    Dependency that optionally includes authentication. Use for endpoints that work with or without auth.

    Args:
        user: Optional user information from JWT token

    Returns:
        User information dict or None
    """
    return user


async def validate_session_token(session_token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a NextAuth.js session token by checking the database.
    This is an alternative to JWT validation for session-based auth.

    Note: Currently not implemented - JWT validation is the primary authentication method.
    Implementation would require:
    - Query sessions table with session_token
    - Validate expiration timestamp
    - Join with users table for user information
    - Return user data if valid

    Args:
        session_token: Session token string

    Returns:
        Dict containing user and session information, or None if invalid
    """
    logger.info("Session token validation not implemented, using JWT auth", token_hash=hash(session_token))
    return None


class AuthenticationMiddleware:
    """Middleware to add user context to requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Try to extract user from Authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove "Bearer " prefix
                try:
                    user_info = await verify_nextauth_jwt(token)
                    # Add user info to request state
                    request.state.user = user_info
                    request.state.user_id = user_info.get("sub")
                    request.state.user_email = user_info.get("email")
                except (JWTAuthError, Exception):
                    # Invalid token, but don't reject the request
                    # Let individual endpoints decide if auth is required
                    # Do NOT set user attributes on state
                    pass

        await self.app(scope, receive, send)


def create_jwt_token(user_data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
    """
    Create a JWT token for a user (for testing or special cases).

    Args:
        user_data: User information to encode in token
        expires_delta: Token expiration time in minutes

    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = settings.access_token_expire_minutes

    expire = datetime.now(timezone.utc).timestamp() + (expires_delta * 60)

    to_encode = user_data.copy()
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc).timestamp()})

    encoded_jwt = jwt.encode(to_encode, NEXTAUTH_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_user_permissions(user: Dict[str, Any], required_permissions: list) -> bool:
    """
    Verify that a user has the required permissions.

    Note: Currently returns True for all authenticated users.
    Full implementation planned for multi-tenant phase (Sprint 4+) with:
    - Role-based access control (RBAC)
    - Project-level permissions (owner, editor, viewer)
    - Organization-level permissions
    - Permission inheritance and delegation

    Args:
        user: User information from JWT token
        required_permissions: List of required permission strings

    Returns:
        True if user has all required permissions (currently always True)
    """
    logger.info("Permission check bypassed - all authenticated users allowed",
                user_id=user.get("sub"),
                permissions=required_permissions)
    return True  # MVP: All authenticated users have full access