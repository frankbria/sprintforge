"""
Quota enforcement service for project limits.

This module implements:
- Free tier: 3 active projects
- Pro tier: Unlimited projects
- Clear upgrade messaging
- Quota enforcement on project creation
"""

from typing import Dict, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.project import Project
from app.models.user import User

logger = structlog.get_logger(__name__)


class QuotaService:
    """Service for managing and enforcing user quotas."""

    # Quota limits by tier
    TIER_LIMITS = {
        "free": 3,
        "pro": None,  # Unlimited
        "enterprise": None,  # Unlimited
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize quota service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_user_tier(self, user_id: UUID) -> str:
        """
        Get user's subscription tier.

        Args:
            user_id: User ID

        Returns:
            Subscription tier (free, pro, enterprise)

        Raises:
            HTTPException: If user not found
        """
        result = await self.db.execute(
            select(User.subscription_tier).where(User.id == user_id)
        )
        tier = result.scalar_one_or_none()

        if tier is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return tier

    async def get_project_count(self, user_id: UUID) -> int:
        """
        Get count of active projects for a user.

        Args:
            user_id: User ID

        Returns:
            Number of active projects
        """
        result = await self.db.execute(
            select(func.count(Project.id)).where(Project.owner_id == user_id)
        )
        count = result.scalar_one()

        return count

    async def get_quota_status(self, user_id: UUID) -> Dict:
        """
        Get detailed quota status for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with quota information:
            {
                "tier": "free|pro|enterprise",
                "limit": int or None (unlimited),
                "used": int,
                "remaining": int or None (unlimited),
                "percentage": float or None
            }
        """
        tier = await self.get_user_tier(user_id)
        limit = self.TIER_LIMITS.get(tier, 3)  # Default to free tier
        used = await self.get_project_count(user_id)

        status = {
            "tier": tier,
            "limit": limit,
            "used": used,
        }

        if limit is None:
            # Unlimited tier
            status["remaining"] = None
            status["percentage"] = None
        else:
            status["remaining"] = max(0, limit - used)
            status["percentage"] = (used / limit * 100) if limit > 0 else 0

        return status

    async def check_project_quota(self, user_id: UUID) -> None:
        """
        Check if user can create a new project.

        Args:
            user_id: User ID

        Raises:
            HTTPException: 403 if quota exceeded
        """
        tier = await self.get_user_tier(user_id)
        limit = self.TIER_LIMITS.get(tier, 3)

        # Pro and enterprise have unlimited projects
        if limit is None:
            return

        count = await self.get_project_count(user_id)

        if count >= limit:
            logger.warning(
                "Project quota exceeded",
                user_id=str(user_id),
                tier=tier,
                count=count,
                limit=limit
            )

            raise HTTPException(
                status_code=403,
                detail={
                    "error": "quota_exceeded",
                    "message": f"Free tier allows {limit} active projects. You currently have {count} projects.",
                    "current": count,
                    "limit": limit,
                    "tier": tier,
                    "upgrade_url": "/pricing",
                    "upgrade_message": "Upgrade to Pro for unlimited projects"
                }
            )

        logger.info(
            "Project quota check passed",
            user_id=str(user_id),
            tier=tier,
            count=count,
            limit=limit,
            remaining=limit - count
        )

    async def can_create_project(self, user_id: UUID) -> bool:
        """
        Check if user can create a project without raising exception.

        Args:
            user_id: User ID

        Returns:
            True if user can create project, False otherwise
        """
        try:
            await self.check_project_quota(user_id)
            return True
        except HTTPException:
            return False
