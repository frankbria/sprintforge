"""Notification system models for SprintForge."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
import enum

from sqlalchemy import Boolean, String, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.types import UUID as DBUUIDType, JSONB

try:
    from app.database.connection import Base
except ImportError:
    # For testing without database setup
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class NotificationType(str, enum.Enum):
    """Types of notifications in the system."""
    SPRINT_COMPLETE = "sprint_complete"
    PROJECT_SHARED = "project_shared"
    SYSTEM_ALERT = "system_alert"


class NotificationStatus(str, enum.Enum):
    """Status of a notification."""
    UNREAD = "unread"
    READ = "read"


class NotificationChannel(str, enum.Enum):
    """Delivery channels for notifications."""
    EMAIL = "email"
    IN_APP = "in_app"


class Notification(Base):
    """In-app notifications for users."""

    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=NotificationStatus.UNREAD.value, nullable=False, index=True
    )
    meta_data: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    logs = relationship("NotificationLog", back_populates="notification", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize notification, handling metadata parameter."""
        # Handle metadata -> meta_data mapping
        if 'metadata' in kwargs:
            kwargs['meta_data'] = kwargs.pop('metadata')
        super().__init__(**kwargs)

    def __getattribute__(self, name):
        """Override to handle metadata attribute access."""
        if name == 'metadata':
            # Avoid infinite recursion by using object.__getattribute__
            return object.__getattribute__(self, 'meta_data')
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        """Allow setting meta_data via metadata for backward compatibility."""
        if name == 'metadata':
            super().__setattr__('meta_data', value)
        else:
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type='{self.type}', status='{self.status}')>"


class NotificationRule(Base):
    """User-defined rules for notification delivery preferences."""

    __tablename__ = "notification_rules"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    channels: Mapped[list] = mapped_column(
        JSONB, default=lambda: [NotificationChannel.IN_APP.value], nullable=False
    )
    conditions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<NotificationRule(id={self.id}, event_type='{self.event_type}', enabled={self.enabled})>"


class NotificationLog(Base):
    """Log of notification delivery attempts."""

    __tablename__ = "notification_logs"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    notification_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    notification = relationship("Notification", back_populates="logs")

    def __repr__(self) -> str:
        return f"<NotificationLog(id={self.id}, channel='{self.channel}', status='{self.status}')>"


class NotificationTemplate(Base):
    """Email templates for notification types."""

    __tablename__ = "notification_templates"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template_html: Mapped[str] = mapped_column(Text, nullable=False)
    body_template_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<NotificationTemplate(id={self.id}, event_type='{self.event_type}')>"
