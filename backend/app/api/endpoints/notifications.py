"""Notification management endpoints."""

from typing import Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.auth import require_auth
from app.database.connection import get_database_session
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationRuleCreate,
    NotificationRuleUpdate,
    NotificationRuleResponse,
    NotificationRuleListResponse,
    NotificationEventTrigger,
    NotificationEventResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# Notification endpoints
@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationListResponse:
    """
    Get notifications for the current user.

    Query parameters:
    - unread_only: If true, only return unread notifications
    - limit: Maximum number of notifications to return (default: 50)
    - offset: Offset for pagination (default: 0)
    """
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        notifications = await service.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit,
            offset=offset,
        )

        return NotificationListResponse(
            notifications=[
                NotificationResponse.model_validate(n) for n in notifications
            ],
            total=len(notifications),
            limit=limit,
            offset=offset,
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error listing notifications", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationResponse:
    """Get a single notification by ID."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        notification = await service.get_notification(
            notification_id=notification_id,
            user_id=user_id,
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        return NotificationResponse.model_validate(notification)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting notification", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    notification_data: NotificationCreate,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationResponse:
    """
    Create a new notification.

    NOTE: Typically notifications are created automatically by the system
    via notification rules. This endpoint is mainly for admin/testing purposes.
    """
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        # Verify the authenticated user is creating notification for themselves
        if notification_data.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot create notifications for other users"
            )

        notification = await service.create_notification(
            user_id=notification_data.user_id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            metadata=notification_data.metadata,
        )

        return NotificationResponse.model_validate(notification)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating notification", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationResponse:
    """Mark a notification as read."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        notification = await service.mark_as_read(
            notification_id=notification_id,
            user_id=user_id,
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        return NotificationResponse.model_validate(notification)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error marking notification read", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> None:
    """Delete a notification."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        deleted = await service.delete_notification(
            notification_id=notification_id,
            user_id=user_id,
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Notification not found")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting notification", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Notification Rules endpoints
@router.get("/rules/", response_model=NotificationRuleListResponse)
async def list_notification_rules(
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationRuleListResponse:
    """Get all notification rules for the current user."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        rules = await service.get_user_rules(user_id=user_id)

        return NotificationRuleListResponse(
            rules=[NotificationRuleResponse.model_validate(r) for r in rules],
            total=len(rules),
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error listing notification rules", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/rules/", response_model=NotificationRuleResponse, status_code=201)
async def create_notification_rule(
    rule_data: NotificationRuleCreate,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationRuleResponse:
    """Create a new notification rule."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        rule = await service.create_rule(
            user_id=user_id,
            event_type=rule_data.event_type,
            enabled=rule_data.enabled,
            channels=rule_data.channels,
            conditions=rule_data.conditions,
        )

        return NotificationRuleResponse.model_validate(rule)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error creating notification rule", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def update_notification_rule(
    rule_id: UUID,
    rule_data: NotificationRuleUpdate,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationRuleResponse:
    """Update a notification rule."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        rule = await service.update_rule(
            rule_id=rule_id,
            user_id=user_id,
            enabled=rule_data.enabled,
            channels=rule_data.channels,
            conditions=rule_data.conditions,
        )

        if not rule:
            raise HTTPException(status_code=404, detail="Notification rule not found")

        return NotificationRuleResponse.model_validate(rule)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating notification rule", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_notification_rule(
    rule_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> None:
    """Delete a notification rule."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        deleted = await service.delete_rule(
            rule_id=rule_id,
            user_id=user_id,
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Notification rule not found")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting notification rule", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Event trigger endpoint (for system use)
@router.post("/events/trigger", response_model=NotificationEventResponse)
async def trigger_notification_event(
    event: NotificationEventTrigger,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationEventResponse:
    """
    Trigger a notification event to evaluate rules.

    This endpoint is typically called by other system components
    when events occur (e.g., sprint completion, project sharing).
    """
    try:
        service = NotificationService(db)

        result = await service.evaluate_rules(
            event_type=event.event_type,
            event_data=event.event_data,
        )

        return NotificationEventResponse(**result)

    except Exception as e:
        logger.error("Error triggering notification event", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
