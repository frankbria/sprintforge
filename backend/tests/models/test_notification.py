"""
Tests for notification database models.

This test suite validates the Notification, NotificationRule, NotificationLog,
and NotificationTemplate models following TDD principles.

These tests are written BEFORE implementation (RED phase) and should FAIL initially.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# These imports will fail until models are implemented (expected in RED phase)
from app.models.notification import (
    Notification,
    NotificationRule,
    NotificationLog,
    NotificationTemplate,
    NotificationStatus,
    NotificationChannel,
    NotificationType,
)


@pytest.mark.unit
@pytest.mark.database
class TestNotificationModel:
    """Test suite for Notification model."""

    @pytest.mark.asyncio
    async def test_create_notification(self, test_db_session: AsyncSession, test_user):
        """
        Test creating a basic notification.

        Validates that a notification can be created with required fields
        and has proper defaults for status and timestamps.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Sprint 24.Q1.1 Complete",
            message="Sprint 24.Q1.1 has been completed successfully.",
            status=NotificationStatus.UNREAD,
        )

        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        assert notification.id is not None
        assert notification.user_id == test_user.id
        assert notification.type == NotificationType.SPRINT_COMPLETE
        assert notification.title == "Sprint 24.Q1.1 Complete"
        assert notification.message == "Sprint 24.Q1.1 has been completed successfully."
        assert notification.status == NotificationStatus.UNREAD
        assert notification.created_at is not None
        assert isinstance(notification.created_at, datetime)
        assert notification.read_at is None

    @pytest.mark.asyncio
    async def test_notification_defaults(self, test_db_session: AsyncSession, test_user):
        """
        Test notification default values.

        Ensures that status defaults to UNREAD and timestamps are auto-generated.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.PROJECT_SHARED,
            title="Project Shared",
            message="A project was shared with you.",
        )

        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        assert notification.status == NotificationStatus.UNREAD
        assert notification.created_at is not None
        assert notification.read_at is None

    @pytest.mark.asyncio
    async def test_mark_notification_as_read(self, test_db_session: AsyncSession, test_user):
        """
        Test marking a notification as read.

        Validates that status updates to READ and read_at timestamp is set.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Test Notification",
            message="Test message",
        )

        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        # Mark as read
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.utcnow()

        await test_db_session.commit()
        await test_db_session.refresh(notification)

        assert notification.status == NotificationStatus.READ
        assert notification.read_at is not None
        assert isinstance(notification.read_at, datetime)

    @pytest.mark.asyncio
    async def test_notification_with_metadata(self, test_db_session: AsyncSession, test_user):
        """
        Test notification with metadata field.

        Validates that metadata JSON field can store additional context.
        """
        metadata = {
            "project_id": str(uuid4()),
            "sprint_name": "24.Q1.1",
            "completion_percentage": 100,
        }

        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Sprint Complete",
            message="Sprint completed",
            metadata=metadata,
        )

        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        assert notification.metadata == metadata
        assert notification.metadata["project_id"] == metadata["project_id"]
        assert notification.metadata["sprint_name"] == "24.Q1.1"
        assert notification.metadata["completion_percentage"] == 100

    @pytest.mark.asyncio
    async def test_notification_user_relationship(self, test_db_session: AsyncSession, test_user):
        """
        Test notification relationship with user.

        Validates foreign key relationship and cascade behavior.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.PROJECT_SHARED,
            title="Test",
            message="Test message",
        )

        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        # Verify relationship
        assert notification.user_id == test_user.id
        # If eager loading is configured, this should work:
        # assert notification.user.email == test_user.email

    @pytest.mark.asyncio
    async def test_query_notifications_by_user(self, test_db_session: AsyncSession, test_user, test_user_pro):
        """
        Test querying notifications filtered by user.

        Ensures users only see their own notifications.
        """
        # Create notifications for different users
        notif1 = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="User 1 Notification",
            message="Message 1",
        )
        notif2 = Notification(
            user_id=test_user_pro.id,
            type=NotificationType.PROJECT_SHARED,
            title="User 2 Notification",
            message="Message 2",
        )

        test_db_session.add_all([notif1, notif2])
        await test_db_session.commit()

        # Query notifications for test_user
        result = await test_db_session.execute(
            select(Notification).where(Notification.user_id == test_user.id)
        )
        user_notifications = result.scalars().all()

        assert len(user_notifications) == 1
        assert user_notifications[0].title == "User 1 Notification"

    @pytest.mark.asyncio
    async def test_notification_ordering_by_created_at(self, test_db_session: AsyncSession, test_user):
        """
        Test notifications are ordered by created_at descending (newest first).

        Validates default ordering for notification lists.
        """
        # Create multiple notifications with slight time differences
        notif1 = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="First",
            message="First message",
        )
        test_db_session.add(notif1)
        await test_db_session.commit()

        notif2 = Notification(
            user_id=test_user.id,
            type=NotificationType.PROJECT_SHARED,
            title="Second",
            message="Second message",
        )
        test_db_session.add(notif2)
        await test_db_session.commit()

        # Query with descending order
        result = await test_db_session.execute(
            select(Notification)
            .where(Notification.user_id == test_user.id)
            .order_by(Notification.created_at.desc())
        )
        notifications = result.scalars().all()

        assert len(notifications) == 2
        assert notifications[0].title == "Second"  # Most recent first
        assert notifications[1].title == "First"


@pytest.mark.unit
@pytest.mark.database
class TestNotificationRuleModel:
    """Test suite for NotificationRule model."""

    @pytest.mark.asyncio
    async def test_create_notification_rule(self, test_db_session: AsyncSession, test_user):
        """
        Test creating a notification rule.

        Validates basic rule creation with event type and channels.
        """
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        )

        test_db_session.add(rule)
        await test_db_session.commit()
        await test_db_session.refresh(rule)

        assert rule.id is not None
        assert rule.user_id == test_user.id
        assert rule.event_type == NotificationType.SPRINT_COMPLETE
        assert rule.enabled is True
        assert NotificationChannel.EMAIL in rule.channels
        assert NotificationChannel.IN_APP in rule.channels

    @pytest.mark.asyncio
    async def test_notification_rule_defaults(self, test_db_session: AsyncSession, test_user):
        """
        Test notification rule default values.

        Ensures enabled defaults to True and channels defaults to [IN_APP].
        """
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.PROJECT_SHARED,
        )

        test_db_session.add(rule)
        await test_db_session.commit()
        await test_db_session.refresh(rule)

        assert rule.enabled is True
        assert rule.channels == [NotificationChannel.IN_APP]

    @pytest.mark.asyncio
    async def test_notification_rule_with_conditions(self, test_db_session: AsyncSession, test_user):
        """
        Test notification rule with custom conditions.

        Validates that conditions JSON field can store complex filtering rules.
        """
        conditions = {
            "project_ids": [str(uuid4()), str(uuid4())],
            "min_completion_percentage": 80,
            "sprint_pattern": "24.Q*",
        }

        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
            conditions=conditions,
            channels=[NotificationChannel.EMAIL],
        )

        test_db_session.add(rule)
        await test_db_session.commit()
        await test_db_session.refresh(rule)

        assert rule.conditions == conditions
        assert rule.conditions["min_completion_percentage"] == 80
        assert len(rule.conditions["project_ids"]) == 2

    @pytest.mark.asyncio
    async def test_disable_notification_rule(self, test_db_session: AsyncSession, test_user):
        """
        Test disabling a notification rule.

        Validates that rules can be enabled/disabled.
        """
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
        )

        test_db_session.add(rule)
        await test_db_session.commit()
        await test_db_session.refresh(rule)

        # Disable the rule
        rule.enabled = False
        await test_db_session.commit()
        await test_db_session.refresh(rule)

        assert rule.enabled is False

    @pytest.mark.asyncio
    async def test_query_enabled_rules_for_event(self, test_db_session: AsyncSession, test_user):
        """
        Test querying enabled rules for a specific event type.

        Ensures only enabled rules for the event are returned.
        """
        rule1 = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
        )
        rule2 = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=False,  # Disabled
        )
        rule3 = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.PROJECT_SHARED,  # Different event
            enabled=True,
        )

        test_db_session.add_all([rule1, rule2, rule3])
        await test_db_session.commit()

        # Query enabled rules for SPRINT_COMPLETE
        result = await test_db_session.execute(
            select(NotificationRule).where(
                NotificationRule.user_id == test_user.id,
                NotificationRule.event_type == NotificationType.SPRINT_COMPLETE,
                NotificationRule.enabled == True,
            )
        )
        rules = result.scalars().all()

        assert len(rules) == 1
        assert rules[0].id == rule1.id


@pytest.mark.unit
@pytest.mark.database
class TestNotificationLogModel:
    """Test suite for NotificationLog model."""

    @pytest.mark.asyncio
    async def test_create_notification_log(self, test_db_session: AsyncSession, test_user):
        """
        Test creating a notification log entry.

        Validates tracking of notification delivery attempts.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        log = NotificationLog(
            notification_id=notification.id,
            channel=NotificationChannel.EMAIL,
            status="sent",
            sent_at=datetime.utcnow(),
        )

        test_db_session.add(log)
        await test_db_session.commit()
        await test_db_session.refresh(log)

        assert log.id is not None
        assert log.notification_id == notification.id
        assert log.channel == NotificationChannel.EMAIL
        assert log.status == "sent"
        assert log.sent_at is not None
        assert log.error_message is None

    @pytest.mark.asyncio
    async def test_notification_log_with_error(self, test_db_session: AsyncSession, test_user):
        """
        Test logging a failed notification delivery.

        Validates error tracking for failed deliveries.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.PROJECT_SHARED,
            title="Test",
            message="Test message",
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        log = NotificationLog(
            notification_id=notification.id,
            channel=NotificationChannel.EMAIL,
            status="failed",
            sent_at=datetime.utcnow(),
            error_message="SMTP connection timeout",
        )

        test_db_session.add(log)
        await test_db_session.commit()
        await test_db_session.refresh(log)

        assert log.status == "failed"
        assert log.error_message == "SMTP connection timeout"

    @pytest.mark.asyncio
    async def test_notification_log_relationship(self, test_db_session: AsyncSession, test_user):
        """
        Test notification log relationship with notification.

        Validates foreign key relationship.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        log = NotificationLog(
            notification_id=notification.id,
            channel=NotificationChannel.EMAIL,
            status="sent",
            sent_at=datetime.utcnow(),
        )
        test_db_session.add(log)
        await test_db_session.commit()
        await test_db_session.refresh(log)

        assert log.notification_id == notification.id


@pytest.mark.unit
@pytest.mark.database
class TestNotificationTemplateModel:
    """Test suite for NotificationTemplate model."""

    @pytest.mark.asyncio
    async def test_create_notification_template(self, test_db_session: AsyncSession):
        """
        Test creating a notification template.

        Validates template creation with subject and body.
        """
        template = NotificationTemplate(
            event_type=NotificationType.SPRINT_COMPLETE,
            subject_template="Sprint {{ sprint_name }} Complete",
            body_template_html="<p>Sprint {{ sprint_name }} completed {{ completion }}%</p>",
            body_template_text="Sprint {{ sprint_name }} completed {{ completion }}%",
        )

        test_db_session.add(template)
        await test_db_session.commit()
        await test_db_session.refresh(template)

        assert template.id is not None
        assert template.event_type == NotificationType.SPRINT_COMPLETE
        assert "{{ sprint_name }}" in template.subject_template
        assert "{{ sprint_name }}" in template.body_template_html
        assert "{{ completion }}" in template.body_template_text

    @pytest.mark.asyncio
    async def test_query_template_by_event_type(self, test_db_session: AsyncSession):
        """
        Test querying templates by event type.

        Ensures correct template is retrieved for rendering.
        """
        template1 = NotificationTemplate(
            event_type=NotificationType.SPRINT_COMPLETE,
            subject_template="Sprint Complete",
            body_template_html="<p>Sprint completed</p>",
            body_template_text="Sprint completed",
        )
        template2 = NotificationTemplate(
            event_type=NotificationType.PROJECT_SHARED,
            subject_template="Project Shared",
            body_template_html="<p>Project shared</p>",
            body_template_text="Project shared",
        )

        test_db_session.add_all([template1, template2])
        await test_db_session.commit()

        # Query template for SPRINT_COMPLETE
        result = await test_db_session.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.event_type == NotificationType.SPRINT_COMPLETE
            )
        )
        template = result.scalar_one()

        assert template.event_type == NotificationType.SPRINT_COMPLETE
        assert template.subject_template == "Sprint Complete"

    @pytest.mark.asyncio
    async def test_template_unique_event_type(self, test_db_session: AsyncSession):
        """
        Test that event_type is unique (only one template per event).

        Validates uniqueness constraint on event_type.
        """
        template1 = NotificationTemplate(
            event_type=NotificationType.SPRINT_COMPLETE,
            subject_template="Template 1",
            body_template_html="<p>Body 1</p>",
            body_template_text="Body 1",
        )
        test_db_session.add(template1)
        await test_db_session.commit()

        # Try to create duplicate
        template2 = NotificationTemplate(
            event_type=NotificationType.SPRINT_COMPLETE,
            subject_template="Template 2",
            body_template_html="<p>Body 2</p>",
            body_template_text="Body 2",
        )
        test_db_session.add(template2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            await test_db_session.commit()


@pytest.mark.unit
class TestNotificationEnums:
    """Test notification enum types."""

    def test_notification_type_enum(self):
        """Test NotificationType enum values."""
        assert NotificationType.SPRINT_COMPLETE == "sprint_complete"
        assert NotificationType.PROJECT_SHARED == "project_shared"
        assert NotificationType.SYSTEM_ALERT == "system_alert"

    def test_notification_status_enum(self):
        """Test NotificationStatus enum values."""
        assert NotificationStatus.UNREAD == "unread"
        assert NotificationStatus.READ == "read"

    def test_notification_channel_enum(self):
        """Test NotificationChannel enum values."""
        assert NotificationChannel.EMAIL == "email"
        assert NotificationChannel.IN_APP == "in_app"
