"""Pydantic schemas for public sharing."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ShareLinkCreate(BaseModel):
    """Schema for creating a share link."""

    access_type: str = Field(
        default="viewer",
        pattern="^(viewer|editor|commenter)$",
        description="Access level for the share link"
    )
    expires_in_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Number of days until expiration (None = never expires)"
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Optional password protection"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "access_type": "viewer",
            "expires_in_days": 30,
            "password": "secure123"
        }
    })


class ShareLinkUpdate(BaseModel):
    """Schema for updating a share link."""

    access_type: Optional[str] = Field(
        default=None,
        pattern="^(viewer|editor|commenter)$",
        description="Access level for the share link"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="New expiration date (None = never expires)"
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Update password (use empty string to remove)"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "access_type": "editor",
            "expires_at": "2025-03-15T10:00:00Z"
        }
    })


class ShareLinkResponse(BaseModel):
    """Schema for share link response."""

    id: UUID
    project_id: UUID
    token: str
    share_url: str
    access_type: str
    expires_at: Optional[datetime] = None
    password_protected: bool
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "project_id": "660e8400-e29b-41d4-a716-446655440000",
            "token": "a1b2c3d4e5f6g7h8",
            "share_url": "https://sprintforge.com/s/a1b2c3d4e5f6g7h8",
            "access_type": "viewer",
            "expires_at": "2025-03-15T10:00:00Z",
            "password_protected": True,
            "access_count": 42,
            "last_accessed_at": "2025-02-10T15:30:00Z",
            "created_at": "2025-02-05T10:00:00Z"
        }
    })


class ShareLinkListResponse(BaseModel):
    """Schema for listing share links."""

    total: int
    share_links: list[ShareLinkResponse]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total": 3,
            "share_links": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "project_id": "660e8400-e29b-41d4-a716-446655440000",
                    "token": "a1b2c3d4e5f6g7h8",
                    "share_url": "https://sprintforge.com/s/a1b2c3d4e5f6g7h8",
                    "access_type": "viewer",
                    "password_protected": False,
                    "access_count": 10,
                    "created_at": "2025-02-05T10:00:00Z"
                }
            ]
        }
    })


class PublicProjectResponse(BaseModel):
    """Schema for publicly shared project response."""

    project: dict  # Simplified project data
    access_type: str
    can_generate_excel: bool
    can_edit: bool
    can_comment: bool

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "project": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "name": "My Agile Project",
                "description": "Sprint planning for Q1 2025",
                "template_id": "agile_advanced",
                "created_at": "2025-02-03T10:00:00Z",
                "last_generated_at": "2025-02-04T11:30:00Z"
            },
            "access_type": "viewer",
            "can_generate_excel": True,
            "can_edit": False,
            "can_comment": False
        }
    })


class ShareAccessRequest(BaseModel):
    """Schema for accessing a shared project with optional password."""

    password: Optional[str] = Field(
        default=None,
        description="Password if share link is password protected"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "password": "secure123"
        }
    })
