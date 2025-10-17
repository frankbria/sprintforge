"""Sync operations model for Excel-server synchronization."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base
from app.database.types import UUID as DBUUIDType, JSONB


class SyncOperation(Base):
    """Sync operations tracking for Excel-server synchronization."""

    __tablename__ = "sync_operations"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Operation details
    operation_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # upload, download, sync
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False, index=True
    )  # pending, processing, completed, failed

    # File information
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Sync metadata
    sync_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    project = relationship("Project", back_populates="sync_operations")
    user = relationship("User", back_populates="sync_operations")

    def __repr__(self) -> str:
        return f"<SyncOperation(id={self.id}, type='{self.operation_type}', status='{self.status}')>"