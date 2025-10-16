"""Monte Carlo simulation result model."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class SimulationResult(Base):
    """
    Monte Carlo simulation result storage.

    Stores results from Monte Carlo simulations for project schedule analysis,
    including statistical measures and confidence intervals.

    Attributes:
        id: Primary key
        project_id: Foreign key to projects table
        user_id: Foreign key to users table
        iterations: Number of Monte Carlo iterations performed
        task_count: Number of tasks in the simulation
        project_start_date: Start date used for the simulation
        mean_duration: Average project duration across iterations (working days)
        median_duration: Median (P50) project duration
        std_deviation: Standard deviation of project durations
        confidence_intervals: JSON object with percentile values
            (e.g., {10: 45.2, 50: 51.5, 90: 61.5})
        simulation_duration_seconds: Execution time of simulation
        created_at: Timestamp when simulation was performed
    """

    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Simulation parameters
    iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    task_count: Mapped[int] = mapped_column(Integer, nullable=False)
    project_start_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Results
    mean_duration: Mapped[float] = mapped_column(Float, nullable=False)
    median_duration: Mapped[float] = mapped_column(Float, nullable=False)
    std_deviation: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_intervals: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # {10: 45.2, 50: 52.3, 90: 61.5, 95: 65.0, 99: 72.1}

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    simulation_duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    # Relationships
    project = relationship("Project", back_populates="simulation_results")
    user = relationship("User", back_populates="simulation_results")

    # Additional indexes for efficient queries
    __table_args__ = (
        Index(
            "ix_simulation_results_project_created",
            "project_id",
            "created_at",
            postgresql_using="btree",
        ),
        Index(
            "ix_simulation_results_user_created",
            "user_id",
            "created_at",
            postgresql_using="btree",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SimulationResult(id={self.id}, project_id={self.project_id}, "
            f"iterations={self.iterations}, mean_duration={self.mean_duration})>"
        )
