"""Pydantic schemas for Analytics API requests and responses."""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class CriticalPathResponse(BaseModel):
    """Response schema for critical path analysis."""

    critical_tasks: List[UUID] = Field(
        ...,
        description="List of task IDs on the critical path"
    )
    total_duration: int = Field(
        ...,
        ge=0,
        description="Total duration of critical path in days"
    )
    float_time: Dict[str, float] = Field(
        ...,
        description="Mapping of task IDs to their float/slack time in days"
    )
    risk_tasks: List[UUID] = Field(
        ...,
        description="List of high-risk task IDs on critical path"
    )
    path_stability_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Critical path stability score (0-100, higher is more stable)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "critical_tasks": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002",
                ],
                "total_duration": 45,
                "float_time": {
                    "550e8400-e29b-41d4-a716-446655440003": 3.5,
                    "550e8400-e29b-41d4-a716-446655440004": 0.0,
                },
                "risk_tasks": ["550e8400-e29b-41d4-a716-446655440001"],
                "path_stability_score": 78.5,
            }
        }
    )


class ResourceUtilizationResponse(BaseModel):
    """Response schema for resource utilization metrics."""

    total_resources: int = Field(
        ...,
        ge=0,
        description="Total number of resources in the project"
    )
    allocated_resources: int = Field(
        ...,
        ge=0,
        description="Number of resources currently allocated to tasks"
    )
    utilization_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall resource utilization percentage"
    )
    over_allocated: List[Dict[str, Any]] = Field(
        ...,
        description="List of over-allocated resources with details"
    )
    under_utilized: List[Dict[str, Any]] = Field(
        ...,
        description="List of under-utilized resources with details"
    )
    resource_timeline: Dict[str, float] = Field(
        ...,
        description="Mapping of dates to utilization percentages"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_resources": 15,
                "allocated_resources": 12,
                "utilization_pct": 82.5,
                "over_allocated": [
                    {
                        "resource_id": "res_001",
                        "name": "John Doe",
                        "allocation_pct": 120.0,
                        "tasks_count": 5,
                    }
                ],
                "under_utilized": [
                    {
                        "resource_id": "res_003",
                        "name": "Jane Smith",
                        "allocation_pct": 45.0,
                        "tasks_count": 2,
                    }
                ],
                "resource_timeline": {
                    "2025-02-03": 78.5,
                    "2025-02-04": 82.0,
                    "2025-02-05": 85.5,
                },
            }
        }
    )


class SimulationSummaryResponse(BaseModel):
    """Response schema for Monte Carlo simulation summary."""

    percentiles: Dict[str, float] = Field(
        ...,
        description="Duration percentiles from simulation (P10, P50, P75, P90, P95)"
    )
    mean_duration: float = Field(
        ...,
        ge=0.0,
        description="Mean duration from all simulation runs"
    )
    std_deviation: float = Field(
        ...,
        ge=0.0,
        description="Standard deviation of duration distribution"
    )
    risk_level: str = Field(
        ...,
        description="Overall risk level: 'low', 'medium', or 'high'"
    )
    confidence_80pct_range: List[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="80% confidence interval [min, max] in days"
    )
    histogram_data: List[Dict[str, Any]] = Field(
        ...,
        description="Histogram buckets for duration distribution"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "percentiles": {
                    "p10": 38.2,
                    "p50": 45.0,
                    "p75": 52.5,
                    "p90": 58.3,
                    "p95": 62.7,
                },
                "mean_duration": 45.8,
                "std_deviation": 8.2,
                "risk_level": "medium",
                "confidence_80pct_range": [40.5, 55.0],
                "histogram_data": [
                    {"bucket": "35-40", "count": 125},
                    {"bucket": "40-45", "count": 380},
                    {"bucket": "45-50", "count": 420},
                    {"bucket": "50-55", "count": 310},
                    {"bucket": "55-60", "count": 165},
                ],
            }
        }
    )


class ProgressMetricsResponse(BaseModel):
    """Response schema for progress tracking metrics."""

    completion_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall project completion percentage"
    )
    tasks_completed: int = Field(
        ...,
        ge=0,
        description="Number of completed tasks"
    )
    tasks_total: int = Field(
        ...,
        ge=0,
        description="Total number of tasks in project"
    )
    on_time_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of tasks completed on time"
    )
    delayed_tasks: int = Field(
        ...,
        ge=0,
        description="Number of delayed tasks"
    )
    burn_rate: float = Field(
        ...,
        ge=0.0,
        description="Average tasks completed per day"
    )
    estimated_completion_date: date = Field(
        ...,
        description="Estimated project completion date"
    )
    variance_from_plan: int = Field(
        ...,
        description="Days ahead (positive) or behind (negative) schedule"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "completion_pct": 67.5,
                "tasks_completed": 54,
                "tasks_total": 80,
                "on_time_pct": 88.9,
                "delayed_tasks": 6,
                "burn_rate": 2.3,
                "estimated_completion_date": "2025-03-15",
                "variance_from_plan": -3,
            }
        }
    )


class AnalyticsOverviewResponse(BaseModel):
    """Response schema for comprehensive analytics overview."""

    health_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall project health score (0-100, higher is better)"
    )
    critical_path_summary: Dict[str, Any] = Field(
        ...,
        description="Summary of critical path metrics"
    )
    resource_summary: Dict[str, Any] = Field(
        ...,
        description="Summary of resource utilization"
    )
    simulation_summary: Dict[str, Any] = Field(
        ...,
        description="Summary of Monte Carlo simulation results"
    )
    progress_summary: Dict[str, Any] = Field(
        ...,
        description="Summary of progress metrics"
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp when analytics were generated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "health_score": 78.5,
                "critical_path_summary": {
                    "total_duration": 45,
                    "critical_tasks_count": 12,
                    "stability_score": 78.5,
                },
                "resource_summary": {
                    "utilization_pct": 82.5,
                    "over_allocated_count": 1,
                    "under_utilized_count": 3,
                },
                "simulation_summary": {
                    "risk_level": "medium",
                    "p50_duration": 45.0,
                    "p90_duration": 58.3,
                },
                "progress_summary": {
                    "completion_pct": 67.5,
                    "on_time_pct": 88.9,
                    "variance_from_plan": -3,
                },
                "generated_at": "2025-02-03T10:30:00Z",
            }
        }
    )
