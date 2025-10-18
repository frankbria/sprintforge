"""Pydantic schemas for notification API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# Notification schemas
class NotificationBase(BaseModel):
    """Base notification schema."""
    type: str
    title: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""
    user_id: UUID


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""
    status: Optional[str] = None


class NotificationResponse(NotificationBase):
    """Schema for notification responses."""
    id: UUID
    user_id: UUID
    status: str
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for notification list responses."""
    notifications: List[NotificationResponse]
    total: int
    limit: int
    offset: int


# Notification Rule schemas
class NotificationRuleBase(BaseModel):
    """Base notification rule schema."""
    event_type: str
    enabled: bool = True
    channels: List[str] = Field(default_factory=lambda: ["in_app"])
    conditions: Optional[Dict[str, Any]] = None


class NotificationRuleCreate(NotificationRuleBase):
    """Schema for creating a notification rule."""
    pass


class NotificationRuleUpdate(BaseModel):
    """Schema for updating a notification rule."""
    enabled: Optional[bool] = None
    channels: Optional[List[str]] = None
    conditions: Optional[Dict[str, Any]] = None


class NotificationRuleResponse(NotificationRuleBase):
    """Schema for notification rule responses."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationRuleListResponse(BaseModel):
    """Schema for notification rule list responses."""
    rules: List[NotificationRuleResponse]
    total: int


# Event trigger schema
class NotificationEventTrigger(BaseModel):
    """Schema for triggering notification events."""
    event_type: str
    event_data: Dict[str, Any] = Field(
        description="Event data including title, message, and metadata"
    )


class NotificationEventResponse(BaseModel):
    """Schema for event trigger responses."""
    status: str
    event_type: str
    rules_matched: int
    notifications_created: int
    emails_queued: int
