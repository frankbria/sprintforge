"""Notification management endpoints."""

from typing import Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.auth import require_auth
from app.database.connection import get_database_session
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    NotificationRuleCreate,
    NotificationRuleUpdate,
    NotificationRuleResponse,
    NotificationEventTrigger,
)
from app.models.notification import NotificationType, NotificationChannel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])
rules_router = APIRouter(prefix="/notification-rules", tags=["notification-rules"])


# Notification endpoints
@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    status: str = None,  # "unread" or "read" filter
    limit: int = 50,
    offset: int = 0,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> List[NotificationResponse]:
    """
    Get notifications for the current user.

    Query parameters:
    - status: Filter by status ("unread" or "read")
    - limit: Maximum number of notifications to return (default: 50)
    - offset: Offset for pagination (default: 0)
    """
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        # Convert status string to enum if provided
        from app.models.notification import NotificationStatus
        status_enum = None
        if status:
            if status.lower() == "unread":
                status_enum = NotificationStatus.UNREAD
            elif status.lower() == "read":
                status_enum = NotificationStatus.READ

        notifications = await service.get_user_notifications(
            user_id=user_id,
            status=status_enum,
            limit=limit,
            offset=offset,
        )

        # Return simple list, not wrapped object
        return [NotificationResponse.model_validate(n) for n in notifications]

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error listing notifications", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/unread-count")
async def get_unread_count(
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, int]:
    """
    Get count of unread notifications for the current user.

    Returns:
        {"count": <number>}
    """
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        count = await service.get_unread_count(user_id=user_id)

        return {"count": count}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error getting unread count", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationResponse:
    """Mark a notification as read."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        try:
            success = await service.mark_as_read(
                notification_id=notification_id,
                user_id=user_id,
            )

            if not success:
                raise HTTPException(status_code=404, detail="Notification not found")

            # Fetch the updated notification to return
            notification = await service.get_notification(
                notification_id=notification_id,
                user_id=user_id,
            )

            return NotificationResponse.model_validate(notification)

        except PermissionError:
            # User trying to mark another user's notification
            raise HTTPException(status_code=403, detail="Forbidden")

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error("Error marking notification read", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/read-all")
async def mark_all_notifications_read(
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, int]:
    """
    Mark all user notifications as read.

    Returns:
        {"count": <number of notifications marked>}
    """
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        count = await service.mark_all_as_read(user_id=user_id)

        return {"count": count}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error marking all notifications read", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Notification Rules endpoints
@rules_router.get("", response_model=List[NotificationRuleResponse])
async def list_notification_rules(
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> List[NotificationRuleResponse]:
    """Get all notification rules for the current user."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        rules = await service.get_user_rules(user_id=user_id)

        return [NotificationRuleResponse.model_validate(r) for r in rules]

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error("Error listing notification rules", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@rules_router.post("", response_model=NotificationRuleResponse, status_code=201)
async def create_notification_rule(
    rule_data: NotificationRuleCreate,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> NotificationRuleResponse:
    """Create a new notification rule."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        # Convert string event_type to enum
        event_type = NotificationType(rule_data.event_type)

        # Convert channel strings to enums
        channels = [NotificationChannel(ch) for ch in rule_data.channels]

        rule = await service.create_rule(
            user_id=user_id,
            event_type=event_type,
            enabled=rule_data.enabled,
            channels=channels,
            conditions=rule_data.conditions,
        )

        return NotificationRuleResponse.model_validate(rule)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error("Error creating notification rule", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@rules_router.put("/{rule_id}", response_model=NotificationRuleResponse)
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

        # Convert channel strings to enums if provided
        channels = None
        if rule_data.channels is not None:
            channels = [NotificationChannel(ch) for ch in rule_data.channels]

        # Check if rule exists and belongs to user
        existing_rule = await service.get_user_rules(user_id=user_id)
        rule_exists = any(r.id == rule_id for r in existing_rule)

        if not rule_exists:
            # Check if rule exists but belongs to another user
            from sqlalchemy import select
            from app.models.notification import NotificationRule
            result = await db.execute(
                select(NotificationRule).where(NotificationRule.id == rule_id)
            )
            other_rule = result.scalar_one_or_none()

            if other_rule:
                raise HTTPException(status_code=403, detail="Forbidden")
            else:
                raise HTTPException(status_code=404, detail="Notification rule not found")

        rule = await service.update_rule(
            rule_id=rule_id,
            user_id=user_id,
            enabled=rule_data.enabled,
            channels=channels,
            conditions=rule_data.conditions,
        )

        if not rule:
            raise HTTPException(status_code=404, detail="Notification rule not found")

        return NotificationRuleResponse.model_validate(rule)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error("Error updating notification rule", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@rules_router.delete("/{rule_id}", status_code=204)
async def delete_notification_rule(
    rule_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_database_session),
) -> None:
    """Delete a notification rule."""
    try:
        user_id = UUID(user_info.get("sub"))
        service = NotificationService(db)

        # Check if rule exists and belongs to user
        existing_rules = await service.get_user_rules(user_id=user_id)
        rule_exists = any(r.id == rule_id for r in existing_rules)

        if not rule_exists:
            # Check if rule exists but belongs to another user
            from sqlalchemy import select
            from app.models.notification import NotificationRule
            result = await db.execute(
                select(NotificationRule).where(NotificationRule.id == rule_id)
            )
            other_rule = result.scalar_one_or_none()

            if other_rule:
                raise HTTPException(status_code=403, detail="Forbidden")
            else:
                raise HTTPException(status_code=404, detail="Notification rule not found")

        deleted = await service.delete_rule(
            rule_id=rule_id,
            user_id=user_id,
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Notification rule not found")

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error("Error deleting notification rule", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Event trigger endpoint (for system use)
@router.post("/trigger")
async def trigger_notification_event(
    event: NotificationEventTrigger,
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """
    Trigger a notification event to evaluate rules.

    This endpoint is typically called by other system components
    when events occur (e.g., sprint completion, project sharing).
    """
    try:
        service = NotificationService(db)

        # Convert string event_type to enum
        event_type = NotificationType(event.event_type)

        # Evaluate rules and get matching rules
        matching_rules = await service.evaluate_rules(
            event_type=event_type,
            event_data=event.event_data,
        )

        # For now, just count the matching rules
        # In a real implementation, this would create notifications
        # and queue emails based on the matching rules
        return {
            "status": "success",
            "event_type": event.event_type,
            "rules_matched": len(matching_rules),
            "notifications_created": 0,  # Would be implemented in real system
            "emails_queued": 0,  # Would be implemented in real system
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error("Error triggering notification event", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
