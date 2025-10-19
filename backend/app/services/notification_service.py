"""Notification service for managing notifications and rules."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationLog,
    NotificationRule,
    NotificationStatus,
    NotificationTemplate,
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
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            user_id: User ID to send notification to
            notification_type: Notification type enum
            title: Notification title
            message: Notification message
            metadata: Optional metadata dict

        Returns:
            Created Notification instance

        Raises:
            ValueError: If user does not exist
        """
        # Validate user exists
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with id {user_id} does not exist")

        notification = Notification(
            user_id=user_id,
            type=(
                notification_type.value
                if isinstance(notification_type, NotificationType)
                else notification_type
            ),
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
            type=notification.type,
        )

        return notification

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            True if successful

        Raises:
            PermissionError: If notification belongs to different user
        """
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            return False

        # Check authorization
        if notification.user_id != user_id:
            raise PermissionError(
                f"User {user_id} does not have permission to mark notification {notification_id} as read"
            )

        notification.status = NotificationStatus.READ.value
        notification.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(
            "notification_marked_read", notification_id=notification_id, user_id=user_id
        )

        return True

    async def get_user_notifications(
        self,
        user_id: UUID,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: User ID
            status: Optional status filter (UNREAD, READ)
            limit: Maximum number of notifications to return
            offset: Offset for pagination

        Returns:
            List of notifications
        """
        query = select(Notification).where(Notification.user_id == user_id)

        if status is not None:
            query = query.where(Notification.status == status.value)

        query = (
            query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        )

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return list(notifications)

    async def get_unread_count(self, user_id: UUID) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.status == NotificationStatus.UNREAD.value,
                )
            )
        )
        count = result.scalar()
        return count or 0

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        result = await self.db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.status == NotificationStatus.UNREAD.value,
                )
            )
            .values(
                status=NotificationStatus.READ.value, read_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()

        count = result.rowcount

        logger.info("notifications_marked_all_read", user_id=user_id, count=count)

        return count

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
                "notification_deleted", notification_id=notification_id, user_id=user_id
            )
            return True

        return False

    # Notification Rules
    async def create_rule(
        self,
        user_id: UUID,
        event_type: NotificationType,
        enabled: bool = True,
        channels: Optional[List[NotificationChannel]] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> NotificationRule:
        """
        Create a notification rule.

        Args:
            user_id: User ID
            event_type: Event type to trigger on
            enabled: Whether rule is enabled
            channels: List of notification channels
            conditions: Optional conditions dict

        Returns:
            Created NotificationRule instance
        """
        if channels is None:
            channels = [NotificationChannel.IN_APP]

        # Convert channels to list of strings
        channel_values = [
            ch.value if isinstance(ch, NotificationChannel) else ch for ch in channels
        ]

        rule = NotificationRule(
            user_id=user_id,
            event_type=(
                event_type.value
                if isinstance(event_type, NotificationType)
                else event_type
            ),
            enabled=enabled,
            channels=channel_values,
            conditions=conditions or {},
        )

        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(
            "notification_rule_created",
            rule_id=rule.id,
            user_id=user_id,
            event_type=rule.event_type,
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
        channels: Optional[List[NotificationChannel]] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Optional[NotificationRule]:
        """
        Update a notification rule.

        Args:
            rule_id: Rule ID
            user_id: User ID (for authorization)
            enabled: Whether rule is enabled
            channels: List of notification channels
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
                # Convert channels to list of strings
                channel_values = [
                    ch.value if isinstance(ch, NotificationChannel) else ch
                    for ch in channels
                ]
                rule.channels = channel_values
            if conditions is not None:
                rule.conditions = conditions

            await self.db.commit()
            await self.db.refresh(rule)

            logger.info("notification_rule_updated", rule_id=rule_id, user_id=user_id)

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
            logger.info("notification_rule_deleted", rule_id=rule_id, user_id=user_id)
            return True

        return False

    async def evaluate_rules(
        self,
        event_type: NotificationType,
        event_data: Dict[str, Any],
    ) -> List[NotificationRule]:
        """
        Evaluate notification rules for an event and return matching rules.

        Args:
            event_type: Event type
            event_data: Event-specific data for condition matching

        Returns:
            List of matching NotificationRule instances
        """
        # Convert event_type to string if it's an enum
        event_type_str = (
            event_type.value if isinstance(event_type, NotificationType) else event_type
        )

        # Find all enabled rules for this event type
        result = await self.db.execute(
            select(NotificationRule).where(
                and_(
                    NotificationRule.event_type == event_type_str,
                    NotificationRule.enabled.is_(True),
                )
            )
        )
        rules = list(result.scalars().all())

        # Filter rules based on conditions
        matching_rules = []
        for rule in rules:
            if self._rule_matches_conditions(rule, event_data):
                matching_rules.append(rule)

        logger.info(
            "notification_rules_evaluated",
            event_type=event_type_str,
            rules_matched=len(matching_rules),
        )

        return matching_rules

    def _rule_matches_conditions(
        self, rule: NotificationRule, event_data: Dict[str, Any]
    ) -> bool:
        """
        Check if event data matches rule conditions.

        Args:
            rule: NotificationRule to check
            event_data: Event data to match against

        Returns:
            True if rule matches, False otherwise
        """
        if not rule.conditions:
            return True

        # Check project_ids condition
        if "project_ids" in rule.conditions:
            project_id = event_data.get("project_id")
            if project_id not in rule.conditions["project_ids"]:
                return False

        # Check min_completion condition
        if "min_completion" in rule.conditions:
            completion = event_data.get("completion", 0)
            if completion < rule.conditions["min_completion"]:
                return False

        return True

    # Template Management
    async def create_template(
        self,
        event_type: NotificationType,
        subject_template: str,
        body_template_html: str,
        body_template_text: str,
    ) -> NotificationTemplate:
        """
        Create a notification template.

        Args:
            event_type: Event type for the template
            subject_template: Subject line template
            body_template_html: HTML body template
            body_template_text: Plain text body template

        Returns:
            Created NotificationTemplate instance
        """
        event_type_str = (
            event_type.value if isinstance(event_type, NotificationType) else event_type
        )

        template = NotificationTemplate(
            event_type=event_type_str,
            subject_template=subject_template,
            body_template_html=body_template_html,
            body_template_text=body_template_text,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(
            "notification_template_created",
            template_id=template.id,
            event_type=event_type_str,
        )

        return template

    async def get_template(
        self, event_type: NotificationType
    ) -> Optional[NotificationTemplate]:
        """
        Get a notification template by event type.

        Args:
            event_type: Event type to get template for

        Returns:
            NotificationTemplate or None if not found
        """
        event_type_str = (
            event_type.value if isinstance(event_type, NotificationType) else event_type
        )

        result = await self.db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.event_type == event_type_str
            )
        )
        return result.scalar_one_or_none()

    async def update_template(
        self,
        event_type: NotificationType,
        subject_template: Optional[str] = None,
        body_template_html: Optional[str] = None,
        body_template_text: Optional[str] = None,
    ) -> Optional[NotificationTemplate]:
        """
        Update a notification template.

        Args:
            event_type: Event type for the template
            subject_template: Subject line template
            body_template_html: HTML body template
            body_template_text: Plain text body template

        Returns:
            Updated NotificationTemplate or None if not found
        """
        template = await self.get_template(event_type)

        if template:
            if subject_template is not None:
                template.subject_template = subject_template
            if body_template_html is not None:
                template.body_template_html = body_template_html
            if body_template_text is not None:
                template.body_template_text = body_template_text

            await self.db.commit()
            await self.db.refresh(template)

            logger.info(
                "notification_template_updated",
                template_id=template.id,
                event_type=template.event_type,
            )

        return template

    # Delivery Logging
    async def log_delivery(
        self,
        notification_id: UUID,
        channel: NotificationChannel,
        status: str,
        error_message: Optional[str] = None,
    ) -> NotificationLog:
        """
        Log a notification delivery attempt.

        Args:
            notification_id: Notification ID
            channel: Delivery channel
            status: Delivery status (sent, delivered, failed, etc.)
            error_message: Optional error message for failed deliveries

        Returns:
            Created NotificationLog instance
        """
        channel_str = (
            channel.value if isinstance(channel, NotificationChannel) else channel
        )

        log = NotificationLog(
            notification_id=notification_id,
            channel=channel_str,
            status=status,
            sent_at=datetime.now(timezone.utc),
            error_message=error_message,
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        logger.info(
            "notification_delivery_logged",
            log_id=log.id,
            notification_id=notification_id,
            channel=channel_str,
            status=status,
        )

        return log

    async def get_delivery_logs(self, notification_id: UUID) -> List[NotificationLog]:
        """
        Get delivery logs for a notification.

        Args:
            notification_id: Notification ID

        Returns:
            List of NotificationLog instances
        """
        result = await self.db.execute(
            select(NotificationLog)
            .where(NotificationLog.notification_id == notification_id)
            .order_by(NotificationLog.created_at.desc())
        )
        return list(result.scalars().all())
