"""Project baseline models for snapshot and comparison functionality."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, CheckConstraint, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base
from app.database.types import UUID as DBUUIDType, JSONB


class ProjectBaseline(Base):
    """
    Project baseline model for storing project snapshots.

    A baseline is an immutable snapshot of a project's state at a specific point in time.
    It captures all project data, tasks, critical path, and Monte Carlo results for
    future comparison against current project state.
    """

    __tablename__ = "project_baselines"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Snapshot data stored as JSONB for complete project state
    # Contains: project, tasks, critical_path, monte_carlo_results, snapshot_metadata
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Active baseline flag - only one baseline per project can be active
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Snapshot size tracking for monitoring and constraints
    snapshot_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    project = relationship("Project", back_populates="baselines")

    # Constraints
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="baseline_name_not_empty"),
        CheckConstraint("snapshot_size_bytes IS NULL OR snapshot_size_bytes < 10485760", name="snapshot_size_limit"),
        # Unique index for active baseline constraint (only one active baseline per project)
        Index(
            "unique_active_baseline_per_project",
            "project_id",
            unique=True,
            postgresql_where="is_active = true"
        ),
        # GIN index for JSONB queries (optional but useful for future queries)
        Index("idx_baselines_snapshot_data_gin", "snapshot_data", postgresql_using="gin"),
    )

    def to_summary_dict(self) -> dict:
        """
        Return lightweight dict without snapshot data.

        Used for list views where snapshot data would be too large.
        """
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "snapshot_size_bytes": self.snapshot_size_bytes
        }

    def to_full_dict(self) -> dict:
        """
        Return full dict with snapshot data.

        Used for detail views and comparison operations.
        """
        return {
            **self.to_summary_dict(),
            "snapshot_data": self.snapshot_data
        }

    def __repr__(self) -> str:
        return f"<ProjectBaseline(id={self.id}, project_id={self.project_id}, name='{self.name}', is_active={self.is_active})>"
