"""Historical metrics models for velocity tracking and trend analysis."""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import String, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base
from app.database.types import UUID as DBUUIDType, JSONB, TZDateTime


class MetricType(str, Enum):
    """Types of historical metrics tracked."""

    VELOCITY = "velocity"
    COMPLETION_RATE = "completion_rate"
    FORECAST = "forecast"
    BURNDOWN = "burndown"


class ForecastModelType(str, Enum):
    """Types of forecasting models used."""

    LINEAR_REGRESSION = "linear_regression"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"


class HistoricalMetric(Base):
    """Generic time-series metric storage for historical tracking."""

    __tablename__ = "historical_metrics"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), nullable=False, index=True
    )

    # Store additional metadata as JSONB
    # Note: We avoid using "metadata" as attribute name since it's reserved by SQLAlchemy
    metric_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])

    # Composite indexes for efficient time-series queries
    __table_args__ = (
        Index('idx_metrics_project_type_time', 'project_id', 'metric_type', 'timestamp'),
    )


    def __repr__(self) -> str:
        return (
            f"<HistoricalMetric(id={self.id}, project_id={self.project_id}, "
            f"type='{self.metric_type}', value={self.value}, timestamp={self.timestamp})>"
        )


class SprintVelocity(Base):
    """Sprint velocity tracking with points and task completion metrics."""

    __tablename__ = "sprint_velocities"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sprint_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    velocity_points: Mapped[float] = mapped_column(Float, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), nullable=False, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_velocity_project_sprint', 'project_id', 'sprint_id'),
        Index('idx_velocity_project_timestamp', 'project_id', 'timestamp'),
    )

    def __repr__(self) -> str:
        return (
            f"<SprintVelocity(id={self.id}, project_id={self.project_id}, "
            f"sprint_id='{self.sprint_id}', velocity_points={self.velocity_points})>"
        )


class CompletionTrend(Base):
    """Completion rate trends over time periods."""

    __tablename__ = "completion_trends"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Time period
    period_start: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)

    # Completion metrics
    completion_rate: Mapped[float] = mapped_column(Float, nullable=False)
    tasks_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tasks_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])

    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_trend_project_dates', 'project_id', 'period_start', 'period_end'),
    )

    def __repr__(self) -> str:
        return (
            f"<CompletionTrend(id={self.id}, project_id={self.project_id}, "
            f"start={self.period_start}, completion_rate={self.completion_rate})>"
        )


class ForecastData(Base):
    """Forecasting predictions with confidence intervals."""

    __tablename__ = "forecast_data"

    id: Mapped[UUID] = mapped_column(DBUUIDType, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        DBUUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    forecast_date: Mapped[datetime] = mapped_column(
        TZDateTime, nullable=False, index=True
    )
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_lower: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_upper: Mapped[float] = mapped_column(Float, nullable=False)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_forecast_project_date', 'project_id', 'forecast_date'),
    )

    def __repr__(self) -> str:
        return (
            f"<ForecastData(id={self.id}, project_id={self.project_id}, "
            f"date={self.forecast_date}, predicted={self.predicted_value})>"
        )
