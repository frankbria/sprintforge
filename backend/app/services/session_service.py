"""Session management and optimization service."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

import structlog
from sqlalchemy import select, delete, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Session, User
from app.database.connection import get_session_factory

logger = structlog.get_logger(__name__)


class SessionService:
    """Service for session storage optimization and management."""

    @staticmethod
    async def optimize_session_storage(db: AsyncSession) -> Dict[str, int]:
        """Optimize session storage by cleaning up and analyzing patterns."""
        stats = {}

        # Clean up expired sessions
        expired_count = await SessionService.cleanup_expired_sessions(db)
        stats["expired_sessions_cleaned"] = expired_count

        # Clean up duplicate sessions (keep most recent)
        duplicate_count = await SessionService.cleanup_duplicate_sessions(db)
        stats["duplicate_sessions_cleaned"] = duplicate_count

        # Analyze session patterns
        patterns = await SessionService.analyze_session_patterns(db)
        stats.update(patterns)

        logger.info("Session storage optimized", stats=stats)
        return stats

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Remove all expired sessions."""
        now = datetime.now(timezone.utc)

        stmt = delete(Session).where(Session.expires < now)
        result = await db.execute(stmt)
        await db.commit()

        count = result.rowcount
        if count > 0:
            logger.info("Expired sessions cleaned up", count=count)

        return count

    @staticmethod
    async def cleanup_duplicate_sessions(db: AsyncSession) -> int:
        """Clean up duplicate sessions for users, keeping the most recent."""
        # Find users with multiple sessions
        subquery = (
            select(
                Session.user_id,
                func.count(Session.id).label("session_count")
            )
            .where(Session.expires > datetime.now(timezone.utc))
            .group_by(Session.user_id)
            .having(func.count(Session.id) > 1)
            .subquery()
        )

        # Get users with multiple sessions
        result = await db.execute(
            select(subquery.c.user_id, subquery.c.session_count)
        )

        users_with_multiple = result.all()
        total_cleaned = 0

        for user_id, count in users_with_multiple:
            # Keep only the most recent session for each user
            sessions_to_keep = await db.execute(
                select(Session.id)
                .where(
                    and_(
                        Session.user_id == user_id,
                        Session.expires > datetime.now(timezone.utc)
                    )
                )
                .order_by(Session.created_at.desc())
                .limit(1)
            )

            keep_ids = [row[0] for row in sessions_to_keep.all()]

            if keep_ids:
                # Delete all other sessions for this user
                delete_stmt = delete(Session).where(
                    and_(
                        Session.user_id == user_id,
                        Session.expires > datetime.now(timezone.utc),
                        Session.id.notin_(keep_ids)
                    )
                )

                delete_result = await db.execute(delete_stmt)
                cleaned = delete_result.rowcount
                total_cleaned += cleaned

                logger.info(
                    "Cleaned duplicate sessions for user",
                    user_id=str(user_id),
                    kept=1,
                    removed=cleaned
                )

        await db.commit()
        return total_cleaned

    @staticmethod
    async def analyze_session_patterns(db: AsyncSession) -> Dict[str, Any]:
        """Analyze session usage patterns for optimization insights."""
        now = datetime.now(timezone.utc)

        # Total active sessions
        active_count = await db.execute(
            select(func.count(Session.id))
            .where(Session.expires > now)
        )
        active_sessions = active_count.scalar()

        # Sessions by age
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(weeks=1)

        recent_sessions = await db.execute(
            select(func.count(Session.id))
            .where(
                and_(
                    Session.created_at > one_hour_ago,
                    Session.expires > now
                )
            )
        )

        daily_sessions = await db.execute(
            select(func.count(Session.id))
            .where(
                and_(
                    Session.created_at > one_day_ago,
                    Session.expires > now
                )
            )
        )

        weekly_sessions = await db.execute(
            select(func.count(Session.id))
            .where(
                and_(
                    Session.created_at > one_week_ago,
                    Session.expires > now
                )
            )
        )

        # Average session duration
        avg_duration = await db.execute(
            text("""
                SELECT AVG(EXTRACT(EPOCH FROM (expires - created_at))) / 3600 as avg_hours
                FROM sessions
                WHERE expires > :now
            """),
            {"now": now}
        )

        avg_hours = avg_duration.scalar() or 0

        # Users with active sessions
        unique_users = await db.execute(
            select(func.count(func.distinct(Session.user_id)))
            .where(Session.expires > now)
        )

        return {
            "total_active_sessions": active_sessions,
            "sessions_last_hour": recent_sessions.scalar(),
            "sessions_last_day": daily_sessions.scalar(),
            "sessions_last_week": weekly_sessions.scalar(),
            "average_session_duration_hours": round(avg_hours, 2),
            "unique_active_users": unique_users.scalar()
        }

    @staticmethod
    async def get_session_health_metrics(db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive session health and performance metrics."""
        now = datetime.now(timezone.utc)

        # Basic counts
        total_sessions = await db.execute(select(func.count(Session.id)))
        active_sessions = await db.execute(
            select(func.count(Session.id)).where(Session.expires > now)
        )
        expired_sessions = await db.execute(
            select(func.count(Session.id)).where(Session.expires <= now)
        )

        # Session age distribution
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(weeks=1)
        one_month_ago = now - timedelta(days=30)

        sessions_24h = await db.execute(
            select(func.count(Session.id))
            .where(Session.created_at > one_day_ago)
        )

        sessions_7d = await db.execute(
            select(func.count(Session.id))
            .where(Session.created_at > one_week_ago)
        )

        sessions_30d = await db.execute(
            select(func.count(Session.id))
            .where(Session.created_at > one_month_ago)
        )

        # Upcoming expirations (sessions expiring soon)
        one_hour_later = now + timedelta(hours=1)
        expiring_soon = await db.execute(
            select(func.count(Session.id))
            .where(
                and_(
                    Session.expires > now,
                    Session.expires <= one_hour_later
                )
            )
        )

        return {
            "total_sessions": total_sessions.scalar(),
            "active_sessions": active_sessions.scalar(),
            "expired_sessions": expired_sessions.scalar(),
            "sessions_created_24h": sessions_24h.scalar(),
            "sessions_created_7d": sessions_7d.scalar(),
            "sessions_created_30d": sessions_30d.scalar(),
            "sessions_expiring_within_1h": expiring_soon.scalar(),
            "health_ratio": round(
                (active_sessions.scalar() / max(total_sessions.scalar(), 1)) * 100, 2
            )
        }

    @staticmethod
    async def extend_session(
        db: AsyncSession,
        session_token: str,
        hours: int = 24
    ) -> Optional[Session]:
        """Extend session expiration time."""
        session = await db.execute(
            select(Session).where(Session.session_token == session_token)
        )
        session = session.scalar_one_or_none()

        if not session:
            return None

        # Check if session is not already expired
        if session.expires <= datetime.now(timezone.utc):
            logger.warning("Attempted to extend expired session",
                         session_id=str(session.id))
            return None

        # Extend expiration
        session.expires = datetime.now(timezone.utc) + timedelta(hours=hours)
        session.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(session)

        logger.info(
            "Session extended",
            session_id=str(session.id),
            new_expiry=session.expires,
            hours_added=hours
        )

        return session

    @staticmethod
    async def batch_cleanup_sessions(
        db: AsyncSession,
        batch_size: int = 1000
    ) -> int:
        """Perform batch cleanup of expired sessions for performance."""
        total_cleaned = 0
        now = datetime.now(timezone.utc)

        while True:
            # Get batch of expired session IDs
            expired_ids = await db.execute(
                select(Session.id)
                .where(Session.expires < now)
                .limit(batch_size)
            )

            ids_to_delete = [row[0] for row in expired_ids.all()]

            if not ids_to_delete:
                break

            # Delete batch
            delete_stmt = delete(Session).where(Session.id.in_(ids_to_delete))
            result = await db.execute(delete_stmt)
            await db.commit()

            batch_count = result.rowcount
            total_cleaned += batch_count

            logger.info(f"Cleaned batch of expired sessions", count=batch_count)

            # Break if we got fewer results than batch size (last batch)
            if len(ids_to_delete) < batch_size:
                break

        return total_cleaned

    @staticmethod
    async def get_user_session_history(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get session history for a user (for security monitoring)."""
        sessions = await db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
            .limit(limit)
        )

        session_list = sessions.scalars().all()
        now = datetime.now(timezone.utc)

        return [
            {
                "session_id": str(session.id),
                "created_at": session.created_at,
                "expires": session.expires,
                "is_active": session.expires > now,
                "duration_hours": round(
                    (session.expires - session.created_at).total_seconds() / 3600, 2
                ),
                "time_remaining_hours": round(
                    max(0, (session.expires - now).total_seconds() / 3600), 2
                ) if session.expires > now else 0
            }
            for session in session_list
        ]


# Background task for periodic session cleanup
async def periodic_session_cleanup():
    """Background task to periodically clean up expired sessions."""
    while True:
        try:
            session_factory = get_session_factory()
            async with session_factory() as db:
                cleaned = await SessionService.batch_cleanup_sessions(db)
                if cleaned > 0:
                    logger.info("Periodic session cleanup completed", cleaned=cleaned)

                # Also run optimization
                stats = await SessionService.optimize_session_storage(db)
                logger.info("Periodic session optimization completed", stats=stats)

        except Exception as e:
            logger.error("Error in periodic session cleanup", error=str(e))

        # Wait 1 hour before next cleanup
        await asyncio.sleep(3600)