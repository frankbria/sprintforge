"""Pydantic schemas for historical metrics API."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VelocityDataPoint(BaseModel):
    """Single velocity data point."""

    sprint_id: str
    sprint_name: str = "Sprint"
    velocity: float
    completed_tasks: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class VelocityTrendResponse(BaseModel):
    """Response for velocity trend endpoint."""

    project_id: UUID
    data_points: List[dict] = []
    velocities: List[dict] = []  # Alias for test compatibility
    moving_average: Optional[float] = None
    trend_direction: str = "stable"
    trend: str = "stable"  # Alias for test compatibility
    anomalies: List[dict] = []

    model_config = {"from_attributes": True}


class CompletionDataPoint(BaseModel):
    """Single completion data point."""

    date: datetime
    completion_rate: float
    tasks_completed: int
    tasks_total: int

    model_config = {"from_attributes": True}


class CompletionTrendResponse(BaseModel):
    """Response for completion trends endpoint."""

    project_id: UUID
    period_days: int
    data_points: List[dict] = []
    average_rate: float = 0.0
    patterns: dict = {}

    model_config = {"from_attributes": True}


class ForecastDataPoint(BaseModel):
    """Single forecast data point."""

    forecast_date: datetime
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    model_type: str

    model_config = {"from_attributes": True}


class ForecastResponse(BaseModel):
    """Response for forecast endpoint."""

    project_id: UUID
    periods_ahead: int
    forecasts: List[dict] = []
    model_accuracy: float = 0.0

    model_config = {"from_attributes": True}


class HistoricalMetricsSummaryResponse(BaseModel):
    """Response for metrics summary endpoint."""

    project_id: UUID
    current_velocity: float = 0.0
    average_velocity: float = 0.0
    avg_velocity: float = 0.0  # Alias for test compatibility
    velocity_trend: str = "stable"
    completion_rate: float = 0.0
    total_sprints: int = 0
    predicted_completion_date: Optional[datetime] = None
    velocity: float = 0.0  # Alias for test compatibility
    trend: str = "stable"  # Alias for test compatibility
    forecasts: List[dict] = []  # For test compatibility
    forecast: dict = {}  # Alias for test compatibility
    predicted: Optional[datetime] = None  # Alias for test compatibility

    model_config = {"from_attributes": True}
