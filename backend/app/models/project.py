"""Project and membership models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base
from app.database.types import UUID as DBUUIDType, JSONB


class Project(Base):
    """SprintForge project model with JSONB configuration."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Project configuration stored as JSONB for flexibility
    configuration: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Template and version tracking
    template_version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Sharing settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    public_share_token: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    share_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    owner = relationship("User", back_populates="projects")
    memberships = relationship("ProjectMembership", back_populates="project", cascade="all, delete-orphan")
    sync_operations = relationship("SyncOperation", back_populates="project", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", back_populates="project", cascade="all, delete-orphan")
    simulation_results = relationship("SimulationResult", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"


class ProjectMembership(Base):
    """Project membership model for team collaboration."""

    __tablename__ = "project_memberships"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Role-based access control
    role: Mapped[str] = mapped_column(
        String(50), default="viewer", nullable=False, index=True
    )  # owner, admin, editor, viewer

    # Invitation workflow
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False, index=True
    )  # pending, active, declined
    invited_by: Mapped[Optional[UUID]] = mapped_column(
        DBUUIDType, ForeignKey("users.id"), nullable=True
    )
    invited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Permissions (future extensibility)
    permissions: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    project = relationship("Project", back_populates="memberships")
    user = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    def __repr__(self) -> str:
        return f"<ProjectMembership(id={self.id}, project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"