"""
Tests for NotificationService.

This test suite validates the NotificationService business logic layer
for creating, managing, and evaluating notification rules.

These tests are written BEFORE implementation (RED phase) and should FAIL initially.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch

from sqlalchemy.ext.asyncio import AsyncSession

# These imports will fail until service is implemented (expected in RED phase)
from app.services.notification_service import NotificationService
from app.models.notification import (
    Notification,
    NotificationRule,
    NotificationLog,
    NotificationTemplate,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
)


@pytest.mark.unit
class TestNotificationServiceCreation:
    """Test notification creation functionality."""

    @pytest.mark.asyncio
    async def test_create_notification(self, test_db_session: AsyncSession, test_user):
        """
        Test creating a basic notification.

        Validates notification creation with required fields.
        """
        service = NotificationService(test_db_session)

        notification = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Sprint Complete",
            message="Sprint 24.Q1.1 is complete",
            metadata={"sprint_name": "24.Q1.1"},
        )

        assert notification is not None
        assert notification.id is not None
        assert notification.user_id == test_user.id
        assert notification.type == NotificationType.SPRINT_COMPLETE
        assert notification.title == "Sprint Complete"
        assert notification.status == NotificationStatus.UNREAD

    @pytest.mark.asyncio
    async def test_create_notification_with_metadata(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test creating notification with custom metadata.

        Validates metadata storage for context.
        """
        service = NotificationService(test_db_session)

        metadata = {
            "project_id": str(uuid4()),
            "sprint_name": "24.Q1.1",
            "completion": 100,
            "url": "/projects/123/sprints/1",
        }

        notification = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Sprint Complete",
            message="Sprint completed",
            metadata=metadata,
        )

        assert notification.metadata == metadata
        assert notification.metadata["project_id"] == metadata["project_id"]

    @pytest.mark.asyncio
    async def test_create_notification_validates_user(
        self, test_db_session: AsyncSession
    ):
        """
        Test that creating notification validates user exists.

        Validates user existence check.
        """
        service = NotificationService(test_db_session)

        with pytest.raises(ValueError) as exc_info:
            await service.create_notification(
                user_id=uuid4(),  # Non-existent user
                notification_type=NotificationType.SPRINT_COMPLETE,
                title="Test",
                message="Test message",
            )

        assert "user" in str(exc_info.value).lower()


@pytest.mark.unit
class TestNotificationServiceRetrieval:
    """Test notification retrieval and querying."""

    @pytest.mark.asyncio
    async def test_get_user_notifications(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test retrieving notifications for a user.

        Validates filtering by user and ordering.
        """
        service = NotificationService(test_db_session)

        # Create test notifications
        notif1 = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Notification 1",
            message="Message 1",
        )
        notif2 = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.PROJECT_SHARED,
            title="Notification 2",
            message="Message 2",
        )

        notifications = await service.get_user_notifications(test_user.id)

        assert len(notifications) == 2
        # Should be ordered by created_at descending (newest first)
        assert notifications[0].id == notif2.id
        assert notifications[1].id == notif1.id

    @pytest.mark.asyncio
    async def test_get_user_notifications_pagination(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test notification retrieval with pagination.

        Validates limit and offset parameters.
        """
        service = NotificationService(test_db_session)

        # Create 10 notifications
        for i in range(10):
            await service.create_notification(
                user_id=test_user.id,
                notification_type=NotificationType.SPRINT_COMPLETE,
                title=f"Notification {i}",
                message=f"Message {i}",
            )

        # Get first page (limit 5)
        page1 = await service.get_user_notifications(test_user.id, limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = await service.get_user_notifications(test_user.id, limit=5, offset=5)
        assert len(page2) == 5

        # Pages should not overlap
        page1_ids = {n.id for n in page1}
        page2_ids = {n.id for n in page2}
        assert len(page1_ids & page2_ids) == 0

    @pytest.mark.asyncio
    async def test_get_user_notifications_filter_unread(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test retrieving only unread notifications.

        Validates status filtering.
        """
        service = NotificationService(test_db_session)

        # Create notifications
        notif1 = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Unread 1",
            message="Message 1",
        )
        notif2 = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.PROJECT_SHARED,
            title="Unread 2",
            message="Message 2",
        )

        # Mark one as read
        await service.mark_as_read(notif1.id, test_user.id)

        # Get unread only
        unread = await service.get_user_notifications(
            test_user.id, status=NotificationStatus.UNREAD
        )

        assert len(unread) == 1
        assert unread[0].id == notif2.id

    @pytest.mark.asyncio
    async def test_get_notification_count(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test getting count of unread notifications.

        Validates count functionality for badge display.
        """
        service = NotificationService(test_db_session)

        # Create notifications
        for i in range(3):
            await service.create_notification(
                user_id=test_user.id,
                notification_type=NotificationType.SPRINT_COMPLETE,
                title=f"Notification {i}",
                message=f"Message {i}",
            )

        count = await service.get_unread_count(test_user.id)
        assert count == 3


@pytest.mark.unit
class TestNotificationServiceMarkAsRead:
    """Test marking notifications as read."""

    @pytest.mark.asyncio
    async def test_mark_notification_as_read(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test marking a single notification as read.

        Validates status update and read_at timestamp.
        """
        service = NotificationService(test_db_session)

        notification = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
        )

        result = await service.mark_as_read(notification.id, test_user.id)

        assert result is True
        # Refresh to get updated state
        await test_db_session.refresh(notification)
        assert notification.status == NotificationStatus.READ
        assert notification.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_as_read_wrong_user(
        self, test_db_session: AsyncSession, test_user, test_user_pro
    ):
        """
        Test that users cannot mark other users' notifications as read.

        Validates authorization check.
        """
        service = NotificationService(test_db_session)

        notification = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
        )

        # Try to mark as read with different user
        with pytest.raises(PermissionError):
            await service.mark_as_read(notification.id, test_user_pro.id)

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, test_db_session: AsyncSession, test_user):
        """
        Test marking all user notifications as read.

        Validates bulk update functionality.
        """
        service = NotificationService(test_db_session)

        # Create multiple notifications
        for i in range(5):
            await service.create_notification(
                user_id=test_user.id,
                notification_type=NotificationType.SPRINT_COMPLETE,
                title=f"Notification {i}",
                message=f"Message {i}",
            )

        count = await service.mark_all_as_read(test_user.id)

        assert count == 5

        # Verify all are read
        unread_count = await service.get_unread_count(test_user.id)
        assert unread_count == 0


@pytest.mark.unit
class TestNotificationServiceRules:
    """Test notification rule management."""

    @pytest.mark.asyncio
    async def test_create_notification_rule(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test creating a notification rule.

        Validates rule creation with channels and conditions.
        """
        service = NotificationService(test_db_session)

        rule = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            conditions={"min_completion": 80},
            enabled=True,
        )

        assert rule is not None
        assert rule.id is not None
        assert rule.user_id == test_user.id
        assert rule.event_type == NotificationType.SPRINT_COMPLETE
        assert NotificationChannel.EMAIL in rule.channels
        assert rule.enabled is True

    @pytest.mark.asyncio
    async def test_get_user_rules(self, test_db_session: AsyncSession, test_user):
        """
        Test retrieving all rules for a user.

        Validates rule listing.
        """
        service = NotificationService(test_db_session)

        # Create rules
        rule1 = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            channels=[NotificationChannel.EMAIL],
        )
        rule2 = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.PROJECT_SHARED,
            channels=[NotificationChannel.IN_APP],
        )

        rules = await service.get_user_rules(test_user.id)

        assert len(rules) == 2
        rule_ids = {r.id for r in rules}
        assert rule1.id in rule_ids
        assert rule2.id in rule_ids

    @pytest.mark.asyncio
    async def test_update_notification_rule(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test updating a notification rule.

        Validates rule modification.
        """
        service = NotificationService(test_db_session)

        rule = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            channels=[NotificationChannel.EMAIL],
            enabled=True,
        )

        # Update rule
        updated = await service.update_rule(
            rule_id=rule.id,
            user_id=test_user.id,
            channels=[NotificationChannel.IN_APP],
            enabled=False,
        )

        assert updated.enabled is False
        assert updated.channels == [NotificationChannel.IN_APP]

    @pytest.mark.asyncio
    async def test_delete_notification_rule(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test deleting a notification rule.

        Validates rule removal.
        """
        service = NotificationService(test_db_session)

        rule = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            channels=[NotificationChannel.EMAIL],
        )

        result = await service.delete_rule(rule.id, test_user.id)

        assert result is True

        # Verify rule is deleted
        rules = await service.get_user_rules(test_user.id)
        assert len(rules) == 0


@pytest.mark.unit
class TestNotificationServiceRuleEvaluation:
    """Test notification rule evaluation logic."""

    @pytest.mark.asyncio
    async def test_evaluate_rules_simple_match(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test evaluating rules with simple event match.

        Validates basic rule matching.
        """
        service = NotificationService(test_db_session)

        # Create rule
        rule = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            channels=[NotificationChannel.EMAIL],
            conditions={},  # No specific conditions
            enabled=True,
        )

        event_data = {
            "sprint_name": "24.Q1.1",
            "completion": 100,
        }

        # Evaluate rules
        matching_rules = await service.evaluate_rules(
            NotificationType.SPRINT_COMPLETE, event_data
        )

        assert len(matching_rules) > 0
        assert rule.id in [r.id for r in matching_rules]

    @pytest.mark.asyncio
    async def test_evaluate_rules_with_conditions(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test evaluating rules with custom conditions.

        Validates condition matching logic.
        """
        service = NotificationService(test_db_session)

        project_id = str(uuid4())

        # Create rule with specific conditions
        rule = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            channels=[NotificationChannel.EMAIL],
            conditions={
                "project_ids": [project_id],
                "min_completion": 80,
            },
            enabled=True,
        )

        # Matching event data
        event_data_match = {
            "project_id": project_id,
            "sprint_name": "24.Q1.1",
            "completion": 100,
        }

        matching = await service.evaluate_rules(
            NotificationType.SPRINT_COMPLETE, event_data_match
        )
        assert len(matching) == 1

        # Non-matching event data (different project)
        event_data_no_match = {
            "project_id": str(uuid4()),
            "sprint_name": "24.Q1.1",
            "completion": 100,
        }

        matching = await service.evaluate_rules(
            NotificationType.SPRINT_COMPLETE, event_data_no_match
        )
        assert len(matching) == 0

    @pytest.mark.asyncio
    async def test_evaluate_rules_disabled_ignored(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test that disabled rules are not evaluated.

        Validates enabled flag check.
        """
        service = NotificationService(test_db_session)

        # Create disabled rule
        rule = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            channels=[NotificationChannel.EMAIL],
            conditions={},
            enabled=False,  # Disabled
        )

        event_data = {"sprint_name": "24.Q1.1"}

        matching = await service.evaluate_rules(
            NotificationType.SPRINT_COMPLETE, event_data
        )

        assert len(matching) == 0

    @pytest.mark.asyncio
    async def test_evaluate_rules_multiple_users(
        self, test_db_session: AsyncSession, test_user, test_user_pro
    ):
        """
        Test evaluating rules for multiple users.

        Validates multi-user notification scenarios.
        """
        service = NotificationService(test_db_session)

        # Create rules for both users
        rule1 = await service.create_rule(
            user_id=test_user.id,
            event_type=NotificationType.PROJECT_SHARED,
            channels=[NotificationChannel.EMAIL],
        )
        rule2 = await service.create_rule(
            user_id=test_user_pro.id,
            event_type=NotificationType.PROJECT_SHARED,
            channels=[NotificationChannel.EMAIL],
        )

        event_data = {"project_id": str(uuid4())}

        matching = await service.evaluate_rules(
            NotificationType.PROJECT_SHARED, event_data
        )

        assert len(matching) == 2
        user_ids = {r.user_id for r in matching}
        assert test_user.id in user_ids
        assert test_user_pro.id in user_ids


@pytest.mark.unit
class TestNotificationServiceTemplates:
    """Test notification template management."""

    @pytest.mark.asyncio
    async def test_create_template(self, test_db_session: AsyncSession):
        """
        Test creating a notification template.

        Validates template creation.
        """
        service = NotificationService(test_db_session)

        template = await service.create_template(
            event_type=NotificationType.SPRINT_COMPLETE,
            subject_template="Sprint {{ sprint_name }} Complete",
            body_template_html="<p>Sprint {{ sprint_name }} is {{ completion }}% done</p>",
            body_template_text="Sprint {{ sprint_name }} is {{ completion }}% done",
        )

        assert template is not None
        assert template.id is not None
        assert template.event_type == NotificationType.SPRINT_COMPLETE

    @pytest.mark.asyncio
    async def test_get_template_by_event_type(self, test_db_session: AsyncSession):
        """
        Test retrieving template by event type.

        Validates template lookup.
        """
        service = NotificationService(test_db_session)

        created = await service.create_template(
            event_type=NotificationType.SPRINT_COMPLETE,
            subject_template="Sprint Complete",
            body_template_html="<p>Sprint complete</p>",
            body_template_text="Sprint complete",
        )

        template = await service.get_template(NotificationType.SPRINT_COMPLETE)

        assert template is not None
        assert template.id == created.id

    @pytest.mark.asyncio
    async def test_update_template(self, test_db_session: AsyncSession):
        """
        Test updating an existing template.

        Validates template modification.
        """
        service = NotificationService(test_db_session)

        template = await service.create_template(
            event_type=NotificationType.SPRINT_COMPLETE,
            subject_template="Old Subject",
            body_template_html="<p>Old body</p>",
            body_template_text="Old body",
        )

        updated = await service.update_template(
            event_type=NotificationType.SPRINT_COMPLETE,
            subject_template="New Subject",
            body_template_html="<p>New body</p>",
            body_template_text="New body",
        )

        assert updated.subject_template == "New Subject"
        assert updated.body_template_html == "<p>New body</p>"


@pytest.mark.unit
class TestNotificationServiceLogging:
    """Test notification delivery logging."""

    @pytest.mark.asyncio
    async def test_log_notification_sent(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test logging successful notification delivery.

        Validates log creation for sent notifications.
        """
        service = NotificationService(test_db_session)

        notification = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
        )

        log = await service.log_delivery(
            notification_id=notification.id,
            channel=NotificationChannel.EMAIL,
            status="sent",
        )

        assert log is not None
        assert log.notification_id == notification.id
        assert log.channel == NotificationChannel.EMAIL
        assert log.status == "sent"

    @pytest.mark.asyncio
    async def test_log_notification_failed(
        self, test_db_session: AsyncSession, test_user
    ):
        """
        Test logging failed notification delivery.

        Validates error tracking.
        """
        service = NotificationService(test_db_session)

        notification = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
        )

        log = await service.log_delivery(
            notification_id=notification.id,
            channel=NotificationChannel.EMAIL,
            status="failed",
            error_message="SMTP timeout",
        )

        assert log.status == "failed"
        assert log.error_message == "SMTP timeout"

    @pytest.mark.asyncio
    async def test_get_delivery_logs(self, test_db_session: AsyncSession, test_user):
        """
        Test retrieving delivery logs for a notification.

        Validates log retrieval.
        """
        service = NotificationService(test_db_session)

        notification = await service.create_notification(
            user_id=test_user.id,
            notification_type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
        )

        # Create multiple logs
        await service.log_delivery(
            notification_id=notification.id,
            channel=NotificationChannel.EMAIL,
            status="sent",
        )
        await service.log_delivery(
            notification_id=notification.id,
            channel=NotificationChannel.IN_APP,
            status="delivered",
        )

        logs = await service.get_delivery_logs(notification.id)

        assert len(logs) == 2
