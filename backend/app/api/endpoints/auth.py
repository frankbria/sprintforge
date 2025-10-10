"""Authentication endpoints for NextAuth.js integration."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
import structlog

from app.core.auth import require_auth, optional_auth, verify_nextauth_jwt
from app.core.security import get_client_ip
from app.database.connection import get_database_session
from app.models.user import User, Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


class UserResponse(BaseModel):
    """User information response model."""
    id: str
    name: Optional[str] = None
    email: str
    image: Optional[str] = None
    subscription_tier: str
    subscription_status: str
    subscription_expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SessionInfo(BaseModel):
    """Session information response model."""
    user: UserResponse
    expires_at: Optional[datetime] = None
    provider: Optional[str] = None
    access_token: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    """Profile update request model."""
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session)
) -> UserResponse:
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    user_id = user_info.get("sub")

    try:
        # Query user from database
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("User not found in database", user_id=user_id)
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            logger.warning("Inactive user attempted access", user_id=user_id)
            raise HTTPException(status_code=403, detail="User account is inactive")

        logger.info("User profile retrieved", user_id=user_id, email=user.email)

        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            image=user.image,
            subscription_tier=user.subscription_tier,
            subscription_status=user.subscription_status,
            subscription_expires_at=user.subscription_expires_at,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except ValueError:
        logger.error("Invalid user ID format", user_id=user_id)
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error retrieving user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    profile_data: UpdateProfileRequest,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session)
) -> UserResponse:
    """
    Update current authenticated user's profile.

    Allows updating name and preferences.
    """
    user_id = user_info.get("sub")

    try:
        # Query user from database
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        # Update fields if provided
        if profile_data.name is not None:
            user.name = profile_data.name

        if profile_data.preferences is not None:
            # Merge with existing preferences
            current_prefs = user.preferences or {}
            current_prefs.update(profile_data.preferences)
            user.preferences = current_prefs

        # Update timestamp
        user.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(user)

        logger.info("User profile updated", user_id=user_id, updated_fields=profile_data.model_dump(exclude_none=True))

        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            image=user.image,
            subscription_tier=user.subscription_tier,
            subscription_status=user.subscription_status,
            subscription_expires_at=user.subscription_expires_at,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except ValueError:
        logger.error("Invalid user ID format", user_id=user_id)
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error updating user", user_id=user_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/session", response_model=SessionInfo)
async def get_session_info(
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session)
) -> SessionInfo:
    """
    Get current session information including user data and session details.
    """
    user_id = user_info.get("sub")

    try:
        # Query user from database
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_response = UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            image=user.image,
            subscription_tier=user.subscription_tier,
            subscription_status=user.subscription_status,
            subscription_expires_at=user.subscription_expires_at,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

        # Extract session info from JWT
        expires_at = None
        if exp := user_info.get("exp"):
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

        logger.info("Session info retrieved", user_id=user_id)

        return SessionInfo(
            user=user_response,
            expires_at=expires_at,
            provider=user_info.get("provider"),
            access_token=user_info.get("accessToken")
        )

    except ValueError:
        logger.error("Invalid user ID format", user_id=user_id)
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error retrieving session", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate")
async def validate_token(
    request: Request,
    user_info: Optional[Dict[str, Any]] = Depends(optional_auth)
):
    """
    Validate the current JWT token and return basic validation info.

    This endpoint can be used by the frontend to check if a token is still valid.
    """
    client_ip = get_client_ip(request)

    if not user_info:
        logger.info("Token validation failed", client_ip=client_ip)
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    user_id = user_info.get("sub")
    logger.info("Token validation successful", user_id=user_id, client_ip=client_ip)

    return {
        "valid": True,
        "user_id": user_id,
        "email": user_info.get("email"),
        "expires_at": user_info.get("exp")
    }


@router.delete("/session")
async def revoke_session(
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Revoke current session (logout functionality).

    This would typically invalidate the session in the database.
    Since we're using JWT tokens, this is mainly for logging purposes.
    """
    user_id = user_info.get("sub")

    # In a full implementation, you might want to maintain a blacklist of revoked tokens
    # or invalidate database sessions

    logger.info("Session revoked", user_id=user_id)

    return {"message": "Session revoked successfully"}


@router.get("/health")
async def auth_health():
    """
    Health check endpoint for authentication service.
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }