"""Notification service for managing notifications and rules."""

import structlog
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification,
    NotificationRule,
    NotificationStatus,
    NotificationChannel,
    NotificationType,
)
from app.models.user import User

logger = structlog.get_logger(__name__)


class NotificationService:
    """Service for managing notifications and notification rules."""

    def __init__(self, db: AsyncSession):
        """Initialize notification service with database session."""
        self.db = db

    async def create_notification(
        self,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            user_id: User ID to send notification to
            type: Notification type (e.g., 'sprint_complete')
            title: Notification title
            message: Notification message
            metadata: Optional metadata dict

        Returns:
            Created Notification instance
        """
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            meta_data=metadata,
            status=NotificationStatus.UNREAD.value,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(
            "notification_created",
            notification_id=notification.id,
            user_id=user_id,
            type=type
        )

        return notification

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            Updated notification or None if not found/unauthorized
        """
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.status = NotificationStatus.READ.value
            notification.read_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(notification)

            logger.info(
                "notification_marked_read",
                notification_id=notification_id,
                user_id=user_id
            )

        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: User ID
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            offset: Offset for pagination

        Returns:
            List of notifications
        """
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.status == NotificationStatus.UNREAD.value)

        query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return list(notifications)

    async def get_notification(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> Optional[Notification]:
        """
        Get a single notification by ID.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            Notification or None if not found/unauthorized
        """
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def delete_notification(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found/unauthorized
        """
        notification = await self.get_notification(notification_id, user_id)

        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            logger.info(
                "notification_deleted",
                notification_id=notification_id,
                user_id=user_id
            )
            return True

        return False

    # Notification Rules
    async def create_rule(
        self,
        user_id: UUID,
        event_type: str,
        enabled: bool = True,
        channels: Optional[List[str]] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> NotificationRule:
        """
        Create a notification rule.

        Args:
            user_id: User ID
            event_type: Event type to trigger on
            enabled: Whether rule is enabled
            channels: List of channels (default: ['in_app'])
            conditions: Optional conditions dict

        Returns:
            Created NotificationRule instance
        """
        if channels is None:
            channels = [NotificationChannel.IN_APP.value]

        rule = NotificationRule(
            user_id=user_id,
            event_type=event_type,
            enabled=enabled,
            channels=channels,
            conditions=conditions,
        )

        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(
            "notification_rule_created",
            rule_id=rule.id,
            user_id=user_id,
            event_type=event_type
        )

        return rule

    async def get_user_rules(self, user_id: UUID) -> List[NotificationRule]:
        """
        Get all notification rules for a user.

        Args:
            user_id: User ID

        Returns:
            List of NotificationRule instances
        """
        result = await self.db.execute(
            select(NotificationRule)
            .where(NotificationRule.user_id == user_id)
            .order_by(NotificationRule.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_rule(
        self,
        rule_id: UUID,
        user_id: UUID,
        enabled: Optional[bool] = None,
        channels: Optional[List[str]] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Optional[NotificationRule]:
        """
        Update a notification rule.

        Args:
            rule_id: Rule ID
            user_id: User ID (for authorization)
            enabled: Whether rule is enabled
            channels: List of channels
            conditions: Conditions dict

        Returns:
            Updated rule or None if not found/unauthorized
        """
        result = await self.db.execute(
            select(NotificationRule).where(
                and_(
                    NotificationRule.id == rule_id,
                    NotificationRule.user_id == user_id,
                )
            )
        )
        rule = result.scalar_one_or_none()

        if rule:
            if enabled is not None:
                rule.enabled = enabled
            if channels is not None:
                rule.channels = channels
            if conditions is not None:
                rule.conditions = conditions

            await self.db.commit()
            await self.db.refresh(rule)

            logger.info(
                "notification_rule_updated",
                rule_id=rule_id,
                user_id=user_id
            )

        return rule

    async def delete_rule(self, rule_id: UUID, user_id: UUID) -> bool:
        """
        Delete a notification rule.

        Args:
            rule_id: Rule ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found/unauthorized
        """
        result = await self.db.execute(
            select(NotificationRule).where(
                and_(
                    NotificationRule.id == rule_id,
                    NotificationRule.user_id == user_id,
                )
            )
        )
        rule = result.scalar_one_or_none()

        if rule:
            await self.db.delete(rule)
            await self.db.commit()
            logger.info(
                "notification_rule_deleted",
                rule_id=rule_id,
                user_id=user_id
            )
            return True

        return False

    async def evaluate_rules(
        self,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate notification rules for an event and create notifications.

        Args:
            event_type: Event type
            event_data: Event-specific data (should include title, message)

        Returns:
            Dict with evaluation results
        """
        # Find all enabled rules for this event type
        result = await self.db.execute(
            select(NotificationRule).where(
                and_(
                    NotificationRule.event_type == event_type,
                    NotificationRule.enabled == True,
                )
            )
        )
        rules = result.scalars().all()

        notifications_created = 0
        emails_queued = 0

        for rule in rules:
            # TODO: Evaluate conditions if present
            # For now, create notification for all matching rules

            # Create in-app notification if enabled
            if NotificationChannel.IN_APP.value in rule.channels:
                notification = await self.create_notification(
                    user_id=rule.user_id,
                    type=event_type,
                    title=event_data.get('title', f'Event: {event_type}'),
                    message=event_data.get('message', 'New notification'),
                    metadata=event_data.get('metadata', {}),
                )
                notifications_created += 1

                # Queue email if enabled
                if NotificationChannel.EMAIL.value in rule.channels:
                    from app.tasks.notification_tasks import send_notification_email
                    send_notification_email.delay(str(notification.id))
                    emails_queued += 1

        logger.info(
            "notification_rules_evaluated",
            event_type=event_type,
            rules_matched=len(rules),
            notifications_created=notifications_created,
            emails_queued=emails_queued
        )

        return {
            "status": "success",
            "event_type": event_type,
            "rules_matched": len(rules),
            "notifications_created": notifications_created,
            "emails_queued": emails_queued,
        }
