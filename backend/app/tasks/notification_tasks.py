"""Celery tasks for notification processing and delivery."""

import asyncio
import structlog
from typing import Dict, Any
from uuid import UUID

from app.services.celery_app import celery_app
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_notification_email(self, notification_id: str) -> Dict[str, Any]:
    """
    Send email for a notification.

    Args:
        notification_id: UUID of the notification to send

    Returns:
        Dict with status and details
    """
    try:
        # Run async code in sync Celery task
        result = asyncio.run(_send_notification_email_async(notification_id))
        return result
    except Exception as exc:
        logger.error(
            "send_notification_email_failed",
            notification_id=notification_id,
            error=str(exc),
            exc_info=True
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _send_notification_email_async(notification_id: str) -> Dict[str, Any]:
    """
    Async implementation of email sending.

    Args:
        notification_id: UUID of the notification

    Returns:
        Dict with status and details
    """
    from datetime import datetime, timezone as tz
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

    from app.database.connection import get_database_url
    from app.models.notification import Notification, NotificationLog, NotificationChannel
    from app.models.user import User
    from app.services.email_service import get_email_service

    # Create database session
    engine = create_async_engine(get_database_url())
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        try:
            # Fetch notification with user
            result = await session.execute(
                select(Notification, User).join(
                    User, Notification.user_id == User.id
                ).where(Notification.id == UUID(notification_id))
            )
            row = result.first()

            if not row:
                logger.warning("notification_not_found", notification_id=notification_id)
                return {"status": "error", "message": "Notification not found"}

            notification, user = row

            # Send email
            email_service = get_email_service()
            success = await email_service.send_email(
                to_email=user.email,
                subject=notification.title,
                body_html=f"<p>{notification.message}</p>",
                body_text=notification.message,
            )

            # Log delivery attempt
            log = NotificationLog(
                notification_id=notification.id,
                channel=NotificationChannel.EMAIL.value,
                status="sent" if success else "failed",
                sent_at=datetime.now(tz.utc),
                error_message=None if success else "SMTP delivery failed",
            )
            session.add(log)
            await session.commit()

            logger.info(
                "notification_email_sent",
                notification_id=notification_id,
                user_email=user.email,
                success=success
            )

            return {
                "status": "success" if success else "failed",
                "notification_id": notification_id,
                "user_email": user.email,
            }

        except Exception as e:
            logger.error(
                "notification_email_error",
                notification_id=notification_id,
                error=str(e),
                exc_info=True
            )
            # Create failed log
            try:
                log = NotificationLog(
                    notification_id=UUID(notification_id),
                    channel=NotificationChannel.EMAIL.value,
                    status="failed",
                    sent_at=datetime.now(tz.utc),
                    error_message=str(e),
                )
                session.add(log)
                await session.commit()
            except:
                pass  # Best effort logging

            raise
        finally:
            await engine.dispose()


@celery_app.task
def process_notification_rules(event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process notification rules for an event.

    Args:
        event_type: Type of event (e.g., 'sprint_complete')
        event_data: Event-specific data

    Returns:
        Dict with processing results
    """
    try:
        result = asyncio.run(_process_notification_rules_async(event_type, event_data))
        return result
    except Exception as exc:
        logger.error(
            "process_notification_rules_failed",
            event_type=event_type,
            error=str(exc),
            exc_info=True
        )
        raise


async def _process_notification_rules_async(
    event_type: str,
    event_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Async implementation of rule processing.

    Args:
        event_type: Type of event
        event_data: Event data

    Returns:
        Dict with results
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

    from app.database.connection import get_database_url
    from app.models.notification import NotificationRule, Notification, NotificationChannel
    from app.models.user import User

    # Create database session
    engine = create_async_engine(get_database_url())
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        try:
            # Find matching enabled rules
            result = await session.execute(
                select(NotificationRule, User).join(
                    User, NotificationRule.user_id == User.id
                ).where(
                    NotificationRule.event_type == event_type,
                    NotificationRule.enabled == True,
                )
            )
            rules = result.all()

            notifications_created = 0
            emails_queued = 0

            for rule, user in rules:
                # TODO: Evaluate conditions if present
                # For now, just create notification for all matching rules

                # Create in-app notification
                if NotificationChannel.IN_APP.value in rule.channels:
                    notification = Notification(
                        user_id=user.id,
                        type=event_type,
                        title=event_data.get('title', f'Event: {event_type}'),
                        message=event_data.get('message', 'New notification'),
                        meta_data=event_data.get('metadata', {}),
                    )
                    session.add(notification)
                    await session.flush()
                    notifications_created += 1

                    # Queue email if enabled
                    if NotificationChannel.EMAIL.value in rule.channels:
                        send_notification_email.delay(str(notification.id))
                        emails_queued += 1

            await session.commit()

            logger.info(
                "notification_rules_processed",
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

        except Exception as e:
            logger.error(
                "notification_rules_processing_error",
                event_type=event_type,
                error=str(e),
                exc_info=True
            )
            raise
        finally:
            await engine.dispose()
