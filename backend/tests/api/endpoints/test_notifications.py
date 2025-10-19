"""
Tests for notification API endpoints.

This test suite validates REST API endpoints for notifications and notification rules,
following TDD principles.

These tests are written BEFORE implementation (RED phase) and should FAIL initially.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# These imports will fail until endpoints are implemented (expected in RED phase)
from app.models.notification import (
    Notification,
    NotificationRule,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
)


@pytest.mark.api
@pytest.mark.asyncio
class TestNotificationListEndpoint:
    """Test GET /api/v1/notifications endpoint."""

    @pytest.mark.asyncio
    async def test_get_notifications_success(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test retrieving user's notifications.

        Validates successful notification list retrieval.
        """
        # Create test notifications
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Test Notification",
            message="Test message",
        )
        test_db_session.add(notification)
        await test_db_session.commit()

        # Mock authentication (adjust based on your auth implementation)
        # This assumes JWT token or session-based auth
        response = await client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["title"] == "Test Notification"

    @pytest.mark.asyncio
    async def test_get_notifications_pagination(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test notification pagination.

        Validates limit and offset query parameters.
        """
        # Create 15 notifications
        for i in range(15):
            notification = Notification(
                user_id=test_user.id,
                type=NotificationType.SPRINT_COMPLETE,
                title=f"Notification {i}",
                message=f"Message {i}",
            )
            test_db_session.add(notification)
        await test_db_session.commit()

        # Get first page
        response = await client.get(
            "/api/v1/notifications?limit=10&offset=0",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # Get second page
        response = await client.get(
            "/api/v1/notifications?limit=10&offset=10",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    @pytest.mark.asyncio
    async def test_get_notifications_filter_unread(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test filtering notifications by status.

        Validates status query parameter.
        """
        # Create unread notification
        notif1 = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Unread",
            message="Unread message",
            status=NotificationStatus.UNREAD,
        )
        # Create read notification
        notif2 = Notification(
            user_id=test_user.id,
            type=NotificationType.PROJECT_SHARED,
            title="Read",
            message="Read message",
            status=NotificationStatus.READ,
            read_at=datetime.utcnow(),
        )
        test_db_session.add_all([notif1, notif2])
        await test_db_session.commit()

        response = await client.get(
            "/api/v1/notifications?status=unread",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(n["status"] == "unread" for n in data)

    @pytest.mark.asyncio
    async def test_get_notifications_unauthorized(self, client: AsyncClient):
        """
        Test getting notifications without authentication.

        Validates authentication requirement.
        """
        response = await client.get("/api/v1/notifications")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_notifications_empty_list(
        self, client: AsyncClient, test_user
    ):
        """
        Test getting notifications when user has none.

        Validates empty list response.
        """
        response = await client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.api
@pytest.mark.asyncio
class TestNotificationMarkAsReadEndpoint:
    """Test POST /api/v1/notifications/{id}/read endpoint."""

    @pytest.mark.asyncio
    async def test_mark_notification_as_read_success(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test marking notification as read.

        Validates successful status update.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
            status=NotificationStatus.UNREAD,
        )
        test_db_session.add(notification)
        await test_db_session.commit()
        await test_db_session.refresh(notification)

        response = await client.post(
            f"/api/v1/notifications/{notification.id}/read",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "read"
        assert data["read_at"] is not None

    @pytest.mark.asyncio
    async def test_mark_notification_not_found(
        self, client: AsyncClient, test_user
    ):
        """
        Test marking non-existent notification as read.

        Validates 404 error.
        """
        fake_id = uuid4()
        response = await client.post(
            f"/api/v1/notifications/{fake_id}/read",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_notification_wrong_user(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user, test_user_pro
    ):
        """
        Test marking another user's notification as read.

        Validates authorization check.
        """
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.SPRINT_COMPLETE,
            title="Test",
            message="Test message",
        )
        test_db_session.add(notification)
        await test_db_session.commit()

        response = await client.post(
            f"/api/v1/notifications/{notification.id}/read",
            headers={"Authorization": f"Bearer {test_user_pro.id}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_mark_all_notifications_as_read(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test marking all user notifications as read.

        Validates bulk update endpoint.
        """
        # Create multiple notifications
        for i in range(3):
            notification = Notification(
                user_id=test_user.id,
                type=NotificationType.SPRINT_COMPLETE,
                title=f"Notification {i}",
                message=f"Message {i}",
            )
            test_db_session.add(notification)
        await test_db_session.commit()

        response = await client.post(
            "/api/v1/notifications/read-all",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3


@pytest.mark.api
@pytest.mark.asyncio
class TestNotificationRuleListEndpoint:
    """Test GET /api/v1/notification-rules endpoint."""

    @pytest.mark.asyncio
    async def test_get_notification_rules(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test retrieving user's notification rules.

        Validates rule list retrieval.
        """
        # Create test rule
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
            channels=[NotificationChannel.EMAIL],
        )
        test_db_session.add(rule)
        await test_db_session.commit()

        response = await client.get(
            "/api/v1/notification-rules",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_notification_rules_empty(
        self, client: AsyncClient, test_user
    ):
        """
        Test getting rules when user has none.

        Validates empty list response.
        """
        response = await client.get(
            "/api/v1/notification-rules",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.api
@pytest.mark.asyncio
class TestNotificationRuleCreateEndpoint:
    """Test POST /api/v1/notification-rules endpoint."""

    @pytest.mark.asyncio
    async def test_create_notification_rule_success(
        self, client: AsyncClient, test_user
    ):
        """
        Test creating a notification rule.

        Validates successful rule creation.
        """
        payload = {
            "event_type": "sprint_complete",
            "channels": ["email", "in_app"],
            "enabled": True,
            "conditions": {
                "min_completion": 80,
            },
        }

        response = await client.post(
            "/api/v1/notification-rules",
            json=payload,
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["event_type"] == "sprint_complete"
        assert "email" in data["channels"]
        assert data["enabled"] is True

    @pytest.mark.asyncio
    async def test_create_notification_rule_validation(
        self, client: AsyncClient, test_user
    ):
        """
        Test rule creation with invalid data.

        Validates input validation.
        """
        payload = {
            "event_type": "invalid_type",
            "channels": ["invalid_channel"],
        }

        response = await client.post(
            "/api/v1/notification-rules",
            json=payload,
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_notification_rule_defaults(
        self, client: AsyncClient, test_user
    ):
        """
        Test rule creation with default values.

        Validates default enabled=True and channels=[in_app].
        """
        payload = {
            "event_type": "sprint_complete",
        }

        response = await client.post(
            "/api/v1/notification-rules",
            json=payload,
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["enabled"] is True
        assert data["channels"] == ["in_app"]


@pytest.mark.api
@pytest.mark.asyncio
class TestNotificationRuleUpdateEndpoint:
    """Test PUT /api/v1/notification-rules/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_notification_rule_success(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test updating a notification rule.

        Validates successful rule update.
        """
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
            channels=[NotificationChannel.EMAIL],
        )
        test_db_session.add(rule)
        await test_db_session.commit()
        await test_db_session.refresh(rule)

        payload = {
            "enabled": False,
            "channels": ["in_app"],
        }

        response = await client.put(
            f"/api/v1/notification-rules/{rule.id}",
            json=payload,
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["channels"] == ["in_app"]

    @pytest.mark.asyncio
    async def test_update_notification_rule_not_found(
        self, client: AsyncClient, test_user
    ):
        """
        Test updating non-existent rule.

        Validates 404 error.
        """
        fake_id = uuid4()
        payload = {"enabled": False}

        response = await client.put(
            f"/api/v1/notification-rules/{fake_id}",
            json=payload,
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_notification_rule_wrong_user(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user, test_user_pro
    ):
        """
        Test updating another user's rule.

        Validates authorization check.
        """
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
            channels=[NotificationChannel.EMAIL],
        )
        test_db_session.add(rule)
        await test_db_session.commit()

        payload = {"enabled": False}

        response = await client.put(
            f"/api/v1/notification-rules/{rule.id}",
            json=payload,
            headers={"Authorization": f"Bearer {test_user_pro.id}"},
        )

        assert response.status_code == 403


@pytest.mark.api
@pytest.mark.asyncio
class TestNotificationRuleDeleteEndpoint:
    """Test DELETE /api/v1/notification-rules/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_notification_rule_success(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test deleting a notification rule.

        Validates successful rule deletion.
        """
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
            channels=[NotificationChannel.EMAIL],
        )
        test_db_session.add(rule)
        await test_db_session.commit()
        await test_db_session.refresh(rule)

        response = await client.delete(
            f"/api/v1/notification-rules/{rule.id}",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_notification_rule_not_found(
        self, client: AsyncClient, test_user
    ):
        """
        Test deleting non-existent rule.

        Validates 404 error.
        """
        fake_id = uuid4()

        response = await client.delete(
            f"/api/v1/notification-rules/{fake_id}",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_notification_rule_wrong_user(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user, test_user_pro
    ):
        """
        Test deleting another user's rule.

        Validates authorization check.
        """
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
            channels=[NotificationChannel.EMAIL],
        )
        test_db_session.add(rule)
        await test_db_session.commit()

        response = await client.delete(
            f"/api/v1/notification-rules/{rule.id}",
            headers={"Authorization": f"Bearer {test_user_pro.id}"},
        )

        assert response.status_code == 403


@pytest.mark.api
@pytest.mark.asyncio
class TestNotificationUnreadCountEndpoint:
    """Test GET /api/v1/notifications/unread-count endpoint."""

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test getting count of unread notifications.

        Validates unread count endpoint for badge display.
        """
        # Create unread notifications
        for i in range(3):
            notification = Notification(
                user_id=test_user.id,
                type=NotificationType.SPRINT_COMPLETE,
                title=f"Notification {i}",
                message=f"Message {i}",
                status=NotificationStatus.UNREAD,
            )
            test_db_session.add(notification)
        await test_db_session.commit()

        response = await client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    @pytest.mark.asyncio
    async def test_get_unread_count_zero(
        self, client: AsyncClient, test_user
    ):
        """
        Test unread count when user has no notifications.

        Validates zero count response.
        """
        response = await client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {test_user.id}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0


@pytest.mark.api
@pytest.mark.asyncio
class TestNotificationWebhookTrigger:
    """Test internal webhook/trigger endpoint for creating notifications."""

    @pytest.mark.asyncio
    async def test_trigger_notification_event(
        self, client: AsyncClient, test_db_session: AsyncSession, test_user
    ):
        """
        Test triggering notification event (internal endpoint).

        Validates notification creation via event trigger.
        """
        # Create rule for user
        rule = NotificationRule(
            user_id=test_user.id,
            event_type=NotificationType.SPRINT_COMPLETE,
            enabled=True,
            channels=[NotificationChannel.IN_APP],
        )
        test_db_session.add(rule)
        await test_db_session.commit()

        payload = {
            "event_type": "sprint_complete",
            "event_data": {
                "sprint_name": "24.Q1.1",
                "completion": 100,
            },
        }

        # This might be an internal/admin endpoint
        response = await client.post(
            "/api/v1/notifications/trigger",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},  # Admin auth
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notifications_created"] >= 0
