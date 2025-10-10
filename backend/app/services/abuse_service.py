"""
Abuse detection and prevention service.

This module implements:
- Pattern detection (same user, many projects)
- Flagging suspicious activity
- Admin dashboard support
- Temporary bans for violations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.project import Project
from app.models.user import User

logger = structlog.get_logger(__name__)


class AbuseDetectionService:
    """Service for detecting and preventing abuse."""

    def __init__(self, db: AsyncSession):
        """
        Initialize abuse detection service.

        Args:
            db: Database session
        """
        self.db = db

        # Abuse detection thresholds
        self.rapid_creation_threshold = 5  # projects in 10 minutes
        self.rapid_creation_window = 600  # 10 minutes in seconds
        self.suspicious_count_threshold = 10  # total projects in 1 hour
        self.suspicious_count_window = 3600  # 1 hour in seconds

    async def check_rapid_project_creation(
        self,
        user_id: UUID
    ) -> Dict[str, any]:
        """
        Check for rapid project creation pattern.

        Args:
            user_id: User ID

        Returns:
            Dictionary with detection results:
            {
                "is_suspicious": bool,
                "count": int,
                "threshold": int,
                "window_minutes": int
            }
        """
        window_start = datetime.utcnow() - timedelta(
            seconds=self.rapid_creation_window
        )

        result = await self.db.execute(
            select(func.count(Project.id))
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.created_at >= window_start
                )
            )
        )
        count = result.scalar_one()

        is_suspicious = count >= self.rapid_creation_threshold

        if is_suspicious:
            logger.warning(
                "Rapid project creation detected",
                user_id=str(user_id),
                count=count,
                threshold=self.rapid_creation_threshold,
                window_minutes=self.rapid_creation_window / 60
            )

        return {
            "is_suspicious": is_suspicious,
            "count": count,
            "threshold": self.rapid_creation_threshold,
            "window_minutes": int(self.rapid_creation_window / 60),
        }

    async def check_unusual_project_count(
        self,
        user_id: UUID
    ) -> Dict[str, any]:
        """
        Check for unusual total project count in recent window.

        Args:
            user_id: User ID

        Returns:
            Dictionary with detection results
        """
        window_start = datetime.utcnow() - timedelta(
            seconds=self.suspicious_count_window
        )

        result = await self.db.execute(
            select(func.count(Project.id))
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.created_at >= window_start
                )
            )
        )
        count = result.scalar_one()

        is_suspicious = count >= self.suspicious_count_threshold

        if is_suspicious:
            logger.warning(
                "Unusual project count detected",
                user_id=str(user_id),
                count=count,
                threshold=self.suspicious_count_threshold,
                window_hours=self.suspicious_count_window / 3600
            )

        return {
            "is_suspicious": is_suspicious,
            "count": count,
            "threshold": self.suspicious_count_threshold,
            "window_hours": int(self.suspicious_count_window / 3600),
        }

    async def detect_suspicious_activity(
        self,
        user_id: UUID
    ) -> Dict[str, any]:
        """
        Run all abuse detection checks for a user.

        Args:
            user_id: User ID

        Returns:
            Comprehensive abuse detection results
        """
        rapid_creation = await self.check_rapid_project_creation(user_id)
        unusual_count = await self.check_unusual_project_count(user_id)

        is_suspicious = (
            rapid_creation["is_suspicious"] or
            unusual_count["is_suspicious"]
        )

        result = {
            "user_id": str(user_id),
            "is_suspicious": is_suspicious,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "rapid_creation": rapid_creation,
                "unusual_count": unusual_count,
            }
        }

        if is_suspicious:
            logger.warning(
                "Suspicious activity detected",
                user_id=str(user_id),
                rapid_creation=rapid_creation["is_suspicious"],
                unusual_count=unusual_count["is_suspicious"]
            )

        return result

    async def get_flagged_users(
        self,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get list of users with suspicious activity.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of user information with abuse metrics
        """
        # Get users with high project counts in recent window
        window_start = datetime.utcnow() - timedelta(
            seconds=self.suspicious_count_window
        )

        result = await self.db.execute(
            select(
                Project.owner_id,
                func.count(Project.id).label("project_count"),
                func.max(Project.created_at).label("latest_creation"),
            )
            .where(Project.created_at >= window_start)
            .group_by(Project.owner_id)
            .having(func.count(Project.id) >= self.suspicious_count_threshold)
            .order_by(func.count(Project.id).desc())
            .limit(limit)
        )

        flagged_users = []
        for row in result:
            user_id = row.owner_id

            # Get user details
            user_result = await self.db.execute(
                select(User.email, User.subscription_tier, User.created_at)
                .where(User.id == user_id)
            )
            user_data = user_result.one_or_none()

            if user_data:
                flagged_users.append({
                    "user_id": str(user_id),
                    "email": user_data.email,
                    "subscription_tier": user_data.subscription_tier,
                    "account_created": user_data.created_at.isoformat(),
                    "recent_project_count": row.project_count,
                    "latest_project_creation": row.latest_creation.isoformat(),
                })

        logger.info(
            "Retrieved flagged users",
            count=len(flagged_users),
            window_hours=self.suspicious_count_window / 3600
        )

        return flagged_users

    async def log_suspicious_activity(
        self,
        user_id: UUID,
        activity_type: str,
        details: Dict
    ):
        """
        Log suspicious activity for admin review.

        Args:
            user_id: User ID
            activity_type: Type of suspicious activity
            details: Additional details about the activity

        Note: In production, this should write to a dedicated
        abuse_logs table or external monitoring system.
        """
        logger.warning(
            "Suspicious activity logged",
            user_id=str(user_id),
            activity_type=activity_type,
            details=details,
            timestamp=datetime.utcnow().isoformat()
        )

        # TODO: In production, write to abuse_logs table or external system
        # This allows admin dashboard to query and review flagged activity

    async def should_throttle_user(self, user_id: UUID) -> bool:
        """
        Determine if user should be throttled based on abuse patterns.

        Args:
            user_id: User ID

        Returns:
            True if user should be throttled, False otherwise
        """
        detection_result = await self.detect_suspicious_activity(user_id)

        if detection_result["is_suspicious"]:
            await self.log_suspicious_activity(
                user_id,
                "pattern_detected",
                detection_result
            )
            return True

        return False
