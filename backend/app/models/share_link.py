"""Share link model for public project sharing."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base
from app.database.types import UUID as DBUUIDType


class ShareLink(Base):
    """Share link model for secure project sharing.

    Supports:
    - Multiple share links per project
    - Password protection
    - Expiration dates
    - Access tracking
    - Role-based access (viewer, editor, commenter)
    """

    __tablename__ = "share_links"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Secure URL-safe token (64 characters)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Access Control
    access_type: Mapped[str] = mapped_column(
        String(50), default="viewer", nullable=False
    )  # viewer, editor, commenter
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )  # None = never expires
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # bcrypt hash

    # Tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project = relationship("Project", back_populates="share_links")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<ShareLink(id={self.id}, project_id={self.project_id}, token='{self.token[:8]}...', access_type='{self.access_type}')>"

    def is_expired(self) -> bool:
        """Check if share link has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_password_protected(self) -> bool:
        """Check if share link requires password."""
        return self.password_hash is not None


# Add indexes for common queries
Index("idx_share_links_token_active", ShareLink.token, ShareLink.expires_at)
Index("idx_share_links_project_created", ShareLink.project_id, ShareLink.created_at.desc())
