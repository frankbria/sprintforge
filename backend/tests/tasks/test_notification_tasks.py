"""
Tests for notification Celery tasks.

This test suite validates background tasks for sending notifications
and processing notification rules, following TDD principles.

These tests are written BEFORE implementation (RED phase) and should FAIL initially.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, call
from datetime import datetime
from uuid import uuid4

# These imports will fail until tasks are implemented (expected in RED phase)
from app.tasks.notification_tasks import (
    send_notification_email,
    process_notification_rules,
    batch_send_notifications,
)
from app.models.notification import (
    Notification,
    NotificationRule,
    NotificationLog,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
)


@pytest.mark.unit
class TestSendNotificationEmailTask:
    """Test suite for send_notification_email Celery task."""

    @patch("app.tasks.notification_tasks.EmailService")
    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_send_notification_email_success(
        self, mock_get_db, mock_email_service_class
    ):
        """
        Test successful email notification sending.

        Validates that task retrieves notification, sends email,
        and creates log entry.
        """
        # Setup mocks
        notification_id = uuid4()
        user_email = "user@example.com"

        mock_notification = Mock(spec=Notification)
        mock_notification.id = notification_id
        mock_notification.user_id = uuid4()
        mock_notification.type = NotificationType.SPRINT_COMPLETE
        mock_notification.title = "Sprint Complete"
        mock_notification.message = "Sprint 24.Q1.1 is complete"
        mock_notification.metadata = {"sprint_name": "24.Q1.1"}

        mock_user = Mock()
        mock_user.email = user_email

        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        # Mock database queries
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one.return_value = mock_notification
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Mock email service
        mock_email_service = Mock()
        mock_email_service.send_email = AsyncMock(return_value=True)
        mock_email_service.render_template = Mock(
            side_effect=lambda template, context: template.format(**context)
        )
        mock_email_service_class.return_value = mock_email_service

        # Execute task
        result = await send_notification_email(str(notification_id))

        assert result is True
        mock_email_service.send_email.assert_called_once()

    @patch("app.tasks.notification_tasks.EmailService")
    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_send_notification_email_not_found(
        self, mock_get_db, mock_email_service_class
    ):
        """
        Test handling of non-existent notification.

        Validates error handling when notification doesn't exist.
        """
        notification_id = uuid4()

        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        # Mock notification not found
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        # Execute task
        result = await send_notification_email(str(notification_id))

        assert result is False

    @patch("app.tasks.notification_tasks.EmailService")
    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_send_notification_email_failure(
        self, mock_get_db, mock_email_service_class
    ):
        """
        Test handling of email sending failure.

        Validates error logging and status update.
        """
        notification_id = uuid4()

        mock_notification = Mock(spec=Notification)
        mock_notification.id = notification_id
        mock_notification.user_id = uuid4()
        mock_notification.type = NotificationType.SPRINT_COMPLETE
        mock_notification.title = "Test"
        mock_notification.message = "Test message"
        mock_notification.metadata = {}

        mock_user = Mock()
        mock_user.email = "user@example.com"

        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one.return_value = mock_notification
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Mock email service to fail
        mock_email_service = Mock()
        mock_email_service.send_email = AsyncMock(
            side_effect=Exception("SMTP connection failed")
        )
        mock_email_service_class.return_value = mock_email_service

        # Execute task
        result = await send_notification_email(str(notification_id))

        assert result is False
        # Should create error log entry
        assert mock_db.add.called

    @patch("app.tasks.notification_tasks.NotificationTemplate")
    @patch("app.tasks.notification_tasks.EmailService")
    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_send_notification_with_template(
        self, mock_get_db, mock_email_service_class, mock_template_class
    ):
        """
        Test sending notification with email template.

        Validates template retrieval and rendering.
        """
        notification_id = uuid4()

        mock_notification = Mock(spec=Notification)
        mock_notification.id = notification_id
        mock_notification.user_id = uuid4()
        mock_notification.type = NotificationType.SPRINT_COMPLETE
        mock_notification.title = "Sprint Complete"
        mock_notification.message = "Sprint complete"
        mock_notification.metadata = {"sprint_name": "24.Q1.1", "completion": 100}

        mock_user = Mock()
        mock_user.email = "user@example.com"

        mock_template = Mock()
        mock_template.subject_template = "Sprint {sprint_name} Complete"
        mock_template.body_template_html = "<p>{sprint_name} is {completion}% done</p>"
        mock_template.body_template_text = "{sprint_name} is {completion}% done"

        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one.return_value = mock_notification
        mock_db.execute.return_value.scalar_one_or_none = Mock(
            side_effect=[mock_template, mock_user]
        )

        mock_email_service = Mock()
        mock_email_service.send_email = AsyncMock(return_value=True)
        mock_email_service.render_template = Mock(
            side_effect=lambda template, context: template.format(**context)
        )
        mock_email_service_class.return_value = mock_email_service

        # Execute task
        result = await send_notification_email(str(notification_id))

        assert result is True
        # Verify template was used
        assert mock_email_service.render_template.call_count >= 2  # Subject + body


@pytest.mark.unit
class TestProcessNotificationRulesTask:
    """Test suite for process_notification_rules Celery task."""

    @patch("app.tasks.notification_tasks.send_notification_email")
    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_process_rules_creates_notifications(
        self, mock_get_db, mock_send_task
    ):
        """
        Test processing notification rules creates notifications.

        Validates rule evaluation and notification creation.
        """
        event_type = NotificationType.SPRINT_COMPLETE
        event_data = {
            "project_id": str(uuid4()),
            "sprint_name": "24.Q1.1",
            "completion": 100,
        }

        # Setup mocks
        user_id = uuid4()
        mock_rule = Mock(spec=NotificationRule)
        mock_rule.id = uuid4()
        mock_rule.user_id = user_id
        mock_rule.event_type = event_type
        mock_rule.enabled = True
        mock_rule.channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        mock_rule.conditions = {}

        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        # Mock query to return one matching rule
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            mock_rule
        ]

        # Execute task
        result = await process_notification_rules(event_type.value, event_data)

        assert result > 0  # At least one notification created
        # Verify notification was added to DB
        assert mock_db.add.called

    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_process_rules_no_matching_rules(self, mock_get_db):
        """
        Test processing with no matching rules.

        Validates graceful handling when no rules match.
        """
        event_type = NotificationType.SPRINT_COMPLETE
        event_data = {"sprint_name": "24.Q1.1"}

        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        # Mock query to return empty list
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        # Execute task
        result = await process_notification_rules(event_type.value, event_data)

        assert result == 0  # No notifications created

    @patch("app.tasks.notification_tasks.send_notification_email")
    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_process_rules_with_conditions(self, mock_get_db, mock_send_task):
        """
        Test processing rules with custom conditions.

        Validates condition evaluation logic.
        """
        event_type = NotificationType.SPRINT_COMPLETE
        project_id = str(uuid4())
        event_data = {
            "project_id": project_id,
            "sprint_name": "24.Q1.1",
            "completion": 100,
        }

        # Rule with conditions that should match
        mock_rule_match = Mock(spec=NotificationRule)
        mock_rule_match.id = uuid4()
        mock_rule_match.user_id = uuid4()
        mock_rule_match.event_type = event_type
        mock_rule_match.enabled = True
        mock_rule_match.channels = [NotificationChannel.EMAIL]
        mock_rule_match.conditions = {
            "project_ids": [project_id],
            "min_completion": 80,
        }

        # Rule with conditions that should NOT match
        mock_rule_no_match = Mock(spec=NotificationRule)
        mock_rule_no_match.id = uuid4()
        mock_rule_no_match.user_id = uuid4()
        mock_rule_no_match.event_type = event_type
        mock_rule_no_match.enabled = True
        mock_rule_no_match.channels = [NotificationChannel.EMAIL]
        mock_rule_no_match.conditions = {
            "project_ids": [str(uuid4())],  # Different project
        }

        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            mock_rule_match,
            mock_rule_no_match,
        ]

        # Execute task
        result = await process_notification_rules(event_type.value, event_data)

        # Only one notification should be created (for matching rule)
        assert result == 1
        assert mock_db.add.call_count == 1

    @patch("app.tasks.notification_tasks.send_notification_email")
    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_process_rules_disabled_rules_ignored(
        self, mock_get_db, mock_send_task
    ):
        """
        Test that disabled rules are not processed.

        Validates enabled flag enforcement.
        """
        event_type = NotificationType.SPRINT_COMPLETE
        event_data = {"sprint_name": "24.Q1.1"}

        # Disabled rule
        mock_rule = Mock(spec=NotificationRule)
        mock_rule.id = uuid4()
        mock_rule.user_id = uuid4()
        mock_rule.event_type = event_type
        mock_rule.enabled = False  # Disabled
        mock_rule.channels = [NotificationChannel.EMAIL]
        mock_rule.conditions = {}

        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        # Query should already filter out disabled rules
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        # Execute task
        result = await process_notification_rules(event_type.value, event_data)

        assert result == 0
        assert not mock_db.add.called


@pytest.mark.unit
class TestBatchSendNotificationsTask:
    """Test suite for batch_send_notifications Celery task."""

    @patch("app.tasks.notification_tasks.send_notification_email")
    @patch("app.tasks.notification_tasks.get_db_session")
    @pytest.mark.asyncio
    async def test_batch_send_notifications(self, mock_get_db, mock_send_task):
        """
        Test batch sending multiple notifications.

        Validates bulk notification processing.
        """
        notification_ids = [uuid4() for _ in range(5)]

        # Execute task
        result = await batch_send_notifications([str(nid) for nid in notification_ids])

        assert result == len(notification_ids)
        assert mock_send_task.delay.call_count == len(notification_ids)

    @patch("app.tasks.notification_tasks.send_notification_email")
    @pytest.mark.asyncio
    async def test_batch_send_empty_list(self, mock_send_task):
        """
        Test batch sending with empty notification list.

        Validates graceful handling of empty input.
        """
        result = await batch_send_notifications([])

        assert result == 0
        assert not mock_send_task.delay.called

    @patch("app.tasks.notification_tasks.send_notification_email")
    @pytest.mark.asyncio
    async def test_batch_send_handles_failures(self, mock_send_task):
        """
        Test batch sending continues despite individual failures.

        Validates error resilience in batch processing.
        """
        notification_ids = [str(uuid4()) for _ in range(3)]

        # First task fails, others succeed
        mock_send_task.delay = Mock(
            side_effect=[
                Exception("Task failed"),
                Mock(),
                Mock(),
            ]
        )

        # Should continue processing despite failure
        # Implementation should handle this gracefully
        result = await batch_send_notifications(notification_ids)

        # At minimum, should attempt all
        assert mock_send_task.delay.call_count == len(notification_ids)


@pytest.mark.unit
class TestCeleryTaskConfiguration:
    """Test Celery task configuration and setup."""

    def test_celery_app_configuration(self):
        """
        Test Celery app is properly configured.

        Validates broker, backend, and task settings.
        """
        from app.services.celery_app import celery_app

        assert celery_app is not None
        assert celery_app.conf.broker_url is not None
        assert celery_app.conf.result_backend is not None

    def test_task_registration(self):
        """
        Test that notification tasks are registered with Celery.

        Validates task discovery and registration.
        """
        from app.services.celery_app import celery_app

        registered_tasks = celery_app.tasks.keys()

        assert "app.tasks.notification_tasks.send_notification_email" in registered_tasks
        assert (
            "app.tasks.notification_tasks.process_notification_rules"
            in registered_tasks
        )

    def test_task_retry_configuration(self):
        """
        Test task retry configuration.

        Validates retry policy for failed tasks.
        """
        # Check if send_notification_email has retry configuration
        assert hasattr(send_notification_email, "max_retries")
        assert send_notification_email.max_retries >= 3

    def test_task_rate_limiting(self):
        """
        Test task rate limiting configuration.

        Validates rate limits to prevent email flooding.
        """
        # Check if tasks have rate limiting configured
        # This might not be in MVP
        pytest.skip("Rate limiting not in MVP")


@pytest.mark.integration
class TestNotificationTasksIntegration:
    """Integration tests for notification tasks with database."""

    @pytest.mark.asyncio
    async def test_end_to_end_notification_flow(
        self, test_db_session, test_user, test_project
    ):
        """
        Test complete notification flow from rule to delivery.

        Validates end-to-end integration of rules, tasks, and email service.
        """
        # This will be implemented after models and services exist
        pytest.skip("Integration test requires full implementation")

    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self, test_db_session):
        """
        Test multiple tasks executing concurrently.

        Validates thread safety and database transaction handling.
        """
        pytest.skip("Concurrency test requires full implementation")
