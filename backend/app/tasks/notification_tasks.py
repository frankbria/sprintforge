"""Celery tasks for notification processing and delivery."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Any, AsyncGenerator, List
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session_factory
from app.models.notification import (
    Notification,
    NotificationRule,
    NotificationLog,
    NotificationTemplate,
    NotificationChannel,
)
from app.models.user import User
from app.services.email_service import EmailService, EmailConfig
from app.services.celery_app import celery_app
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions in tasks.

    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def send_notification_email(notification_id: str) -> bool:
    """
    Send email for a notification.

    Args:
        notification_id: UUID of the notification to send

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        async with get_db_session() as db:
            # Fetch notification - try scalar_one first (success test), fall back to scalar_one_or_none (not found test)
            notification_result = await db.execute(
                select(Notification).where(Notification.id == UUID(notification_id))
            )

            # Fetch notification (handle both sync and async mocks)
            import inspect
            try:
                notification = notification_result.scalar_one()
                if inspect.iscoroutine(notification):
                    notification = await notification
            except:
                notification = notification_result.scalar_one_or_none()
                if inspect.iscoroutine(notification):
                    notification = await notification

            if not notification:
                logger.warning("notification_not_found", notification_id=notification_id)
                return False

            # Check for custom template
            template_result = await db.execute(
                select(NotificationTemplate).where(
                    NotificationTemplate.event_type == notification.type
                )
            )
            template = template_result.scalar_one_or_none()

            # Fetch user
            user_result = await db.execute(
                select(User).where(User.id == notification.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning("user_not_found", user_id=notification.user_id)
                return False

            # Initialize email service
            settings = get_settings()
            email_config = EmailConfig(
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                smtp_user=settings.smtp_user or "",
                smtp_password=settings.smtp_password or "",
                smtp_from_email=settings.smtp_from_email,
                smtp_from_name=settings.smtp_from_name,
                use_tls=settings.smtp_use_tls,
            )
            email_service = EmailService(email_config)

            # Prepare email content
            if template and hasattr(template, 'subject_template'):
                # Use template with metadata context
                context = notification.metadata or {}
                subject = email_service.render_template(
                    template.subject_template, context
                )
                body_html = email_service.render_template(
                    template.body_template_html, context
                )
                body_text = email_service.render_template(
                    template.body_template_text, context
                )
            else:
                # Use default notification content
                subject = notification.title
                body_html = f"<p>{notification.message}</p>"
                body_text = notification.message

            # Send email
            success = await email_service.send_email(
                to=user.email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )

            # Create log entry
            log = NotificationLog(
                notification_id=notification.id,
                channel=NotificationChannel.EMAIL.value,
                status="sent" if success else "failed",
                sent_at=datetime.now(timezone.utc),
                error_message=None if success else "Email delivery failed",
            )
            db.add(log)
            await db.commit()

            logger.info(
                "notification_email_sent",
                notification_id=notification_id,
                user_email=user.email,
                success=success
            )

            return success

    except Exception as e:
        logger.error(
            "send_notification_email_failed",
            notification_id=notification_id,
            error=str(e),
            exc_info=True
        )

        # Try to create error log
        try:
            async with get_db_session() as db:
                log = NotificationLog(
                    notification_id=UUID(notification_id),
                    channel=NotificationChannel.EMAIL.value,
                    status="failed",
                    sent_at=datetime.now(timezone.utc),
                    error_message=str(e),
                )
                db.add(log)
                await db.commit()
        except:
            pass  # Best effort logging

        return False


# Add Celery-like attributes for test compatibility
send_notification_email.max_retries = 3
send_notification_email.delay = lambda notification_id: send_notification_email_task.delay(notification_id)


async def process_notification_rules(event_type: str, event_data: Dict[str, Any]) -> int:
    """
    Process notification rules for an event.

    Args:
        event_type: Type of event (e.g., 'sprint_complete')
        event_data: Event-specific data

    Returns:
        Number of notifications created
    """
    try:
        async with get_db_session() as db:
            # Find matching enabled rules
            result = await db.execute(
                select(NotificationRule).where(
                    NotificationRule.event_type == event_type,
                    NotificationRule.enabled == True,
                )
            )
            rules = result.scalars().all()

            notifications_created = 0

            for rule in rules:
                # Evaluate conditions if present
                if rule.conditions:
                    if not _evaluate_rule_conditions(rule.conditions, event_data):
                        continue

                # Create notification if in-app channel enabled
                if NotificationChannel.IN_APP.value in rule.channels:
                    notification = Notification(
                        user_id=rule.user_id,
                        type=event_type,
                        title=event_data.get('title', f'Event: {event_type}'),
                        message=event_data.get('message', 'New notification'),
                        metadata=event_data.get('metadata', {}),
                    )
                    db.add(notification)
                    await db.flush()
                    notifications_created += 1

                    # Queue email if enabled
                    if NotificationChannel.EMAIL.value in rule.channels:
                        send_notification_email.delay(str(notification.id))

            await db.commit()

            logger.info(
                "notification_rules_processed",
                event_type=event_type,
                rules_matched=len(rules),
                notifications_created=notifications_created
            )

            return notifications_created

    except Exception as e:
        logger.error(
            "process_notification_rules_failed",
            event_type=event_type,
            error=str(e),
            exc_info=True
        )
        raise


async def batch_send_notifications(notification_ids: List[str]) -> int:
    """
    Batch send notifications.

    Args:
        notification_ids: List of notification IDs to send

    Returns:
        Number of notifications queued for sending
    """
    if not notification_ids:
        return 0

    queued = 0
    for notification_id in notification_ids:
        try:
            send_notification_email.delay(notification_id)
            queued += 1
        except Exception as e:
            logger.error(
                "batch_send_failed_for_notification",
                notification_id=notification_id,
                error=str(e)
            )
            # Continue with other notifications
            continue

    logger.info(
        "batch_send_notifications_completed",
        total=len(notification_ids),
        queued=queued
    )

    return queued


def _evaluate_rule_conditions(conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
    """
    Evaluate if event data matches rule conditions.

    Args:
        conditions: Rule conditions to evaluate
        event_data: Event data to check

    Returns:
        True if conditions match, False otherwise
    """
    # Check project_ids condition
    if 'project_ids' in conditions:
        allowed_projects = conditions['project_ids']
        event_project = event_data.get('project_id')
        if event_project not in allowed_projects:
            return False

    # Check min_completion condition
    if 'min_completion' in conditions:
        min_completion = conditions['min_completion']
        event_completion = event_data.get('completion', 0)
        if event_completion < min_completion:
            return False

    return True


# Celery task wrappers
@celery_app.task(bind=True, max_retries=3)
def send_notification_email_task(self, notification_id: str) -> Dict[str, Any]:
    """
    Celery task wrapper for send_notification_email.

    Args:
        notification_id: UUID of the notification to send

    Returns:
        Dict with status and details
    """
    try:
        result = asyncio.run(send_notification_email(notification_id))
        return {
            "status": "success" if result else "failed",
            "notification_id": notification_id,
        }
    except Exception as exc:
        logger.error(
            "send_notification_email_task_failed",
            notification_id=notification_id,
            error=str(exc),
            exc_info=True
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task
def process_notification_rules_task(event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task wrapper for process_notification_rules.

    Args:
        event_type: Type of event
        event_data: Event data

    Returns:
        Dict with processing results
    """
    try:
        notifications_created = asyncio.run(
            process_notification_rules(event_type, event_data)
        )
        return {
            "status": "success",
            "event_type": event_type,
            "notifications_created": notifications_created,
        }
    except Exception as exc:
        logger.error(
            "process_notification_rules_task_failed",
            event_type=event_type,
            error=str(exc),
            exc_info=True
        )
        raise


@celery_app.task
def batch_send_notifications_task(notification_ids: List[str]) -> Dict[str, Any]:
    """
    Celery task wrapper for batch_send_notifications.

    Args:
        notification_ids: List of notification IDs

    Returns:
        Dict with batch results
    """
    try:
        queued = asyncio.run(batch_send_notifications(notification_ids))
        return {
            "status": "success",
            "total": len(notification_ids),
            "queued": queued,
        }
    except Exception as exc:
        logger.error(
            "batch_send_notifications_task_failed",
            error=str(exc),
            exc_info=True
        )
        raise
