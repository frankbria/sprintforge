"""Pydantic schemas for Baseline API requests and responses."""

from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class BaselineBase(BaseModel):
    """Base baseline schema with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Baseline name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Baseline description"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate baseline name is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Baseline name cannot be empty or whitespace-only")
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class CreateBaselineRequest(BaselineBase):
    """Schema for creating a new baseline."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Initial Plan Q4 2025",
                "description": "Baseline created before Sprint 5 starts"
            }
        }
    )


class BaselineResponse(BaselineBase):
    """Schema for baseline API responses (summary without snapshot data)."""

    id: UUID = Field(..., description="Baseline UUID")
    project_id: UUID = Field(..., description="Project UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_active: bool = Field(..., description="Whether this baseline is active for comparison")
    snapshot_size_bytes: Optional[int] = Field(
        default=None,
        description="Size of snapshot data in bytes"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "project_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "name": "Initial Plan Q4 2025",
                "description": "Baseline created before Sprint 5 starts",
                "created_at": "2025-10-17T14:30:00Z",
                "is_active": True,
                "snapshot_size_bytes": 458392
            }
        }
    )


class BaselineDetailResponse(BaselineResponse):
    """Schema for baseline detail responses (includes snapshot data)."""

    snapshot_data: Dict[str, Any] = Field(
        ...,
        description="Complete project snapshot including tasks, critical path, and Monte Carlo results"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "project_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "name": "Initial Plan Q4 2025",
                "description": "Baseline created before Sprint 5 starts",
                "created_at": "2025-10-17T14:30:00Z",
                "is_active": True,
                "snapshot_size_bytes": 458392,
                "snapshot_data": {
                    "project": {
                        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                        "name": "Project Alpha"
                    },
                    "tasks": [
                        {
                            "id": "abc-123",
                            "name": "Task 1",
                            "start_date": "2025-10-20",
                            "end_date": "2025-10-25",
                            "duration": 5,
                            "status": "not_started"
                        }
                    ],
                    "critical_path": ["abc-123"],
                    "snapshot_metadata": {
                        "total_tasks": 100,
                        "completion_pct": 45.5
                    }
                }
            }
        }
    )


class BaselineListResponse(BaseModel):
    """Schema for paginated baseline list responses."""

    total: int = Field(..., description="Total number of baselines")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    baselines: List[BaselineResponse] = Field(..., description="List of baselines")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 2,
                "page": 1,
                "limit": 50,
                "baselines": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "project_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                        "name": "Initial Plan Q4 2025",
                        "description": "Baseline created before Sprint 5 starts",
                        "created_at": "2025-10-17T14:30:00Z",
                        "is_active": True,
                        "snapshot_size_bytes": 458392
                    },
                    {
                        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                        "project_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                        "name": "Mid-Sprint Checkpoint",
                        "description": None,
                        "created_at": "2025-10-20T10:15:00Z",
                        "is_active": False,
                        "snapshot_size_bytes": 492103
                    }
                ]
            }
        }
    )


class SetBaselineActiveResponse(BaseModel):
    """Schema for baseline activation response."""

    id: UUID = Field(..., description="Baseline UUID")
    is_active: bool = Field(..., description="Active status (should be True)")
    message: str = Field(..., description="Success message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "is_active": True,
                "message": "Baseline activated successfully"
            }
        }
    )


class TaskVarianceSchema(BaseModel):
    """Schema for individual task variance in comparison."""

    task_id: str = Field(..., description="Task identifier")
    task_name: str = Field(..., description="Task name")
    variance_days: int = Field(..., description="Total variance in days (negative = ahead, positive = behind)")
    is_ahead: bool = Field(..., description="Whether task is ahead of baseline")
    is_behind: bool = Field(..., description="Whether task is behind baseline")
    start_date_variance: int = Field(..., description="Start date variance in days")
    end_date_variance: int = Field(..., description="End date variance in days")
    duration_variance: int = Field(..., description="Duration variance in days")
    status_changed: bool = Field(..., description="Whether task status changed since baseline")
    dependencies_changed: bool = Field(..., description="Whether task dependencies changed since baseline")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc-123",
                "task_name": "Setup Infrastructure",
                "variance_days": -2,
                "is_ahead": True,
                "is_behind": False,
                "start_date_variance": -1,
                "end_date_variance": -2,
                "duration_variance": 0,
                "status_changed": True,
                "dependencies_changed": False
            }
        }
    )


class ComparisonSummarySchema(BaseModel):
    """Schema for comparison summary statistics."""

    total_tasks: int = Field(..., description="Total number of tasks")
    tasks_ahead: int = Field(..., description="Number of tasks ahead of schedule")
    tasks_behind: int = Field(..., description="Number of tasks behind schedule")
    tasks_on_track: int = Field(..., description="Number of tasks on track")
    avg_variance_days: float = Field(..., description="Average variance in days")
    critical_path_variance_days: float = Field(..., description="Total variance on critical path in days")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_tasks": 100,
                "tasks_ahead": 15,
                "tasks_behind": 10,
                "tasks_on_track": 75,
                "avg_variance_days": -0.5,
                "critical_path_variance_days": 3.0
            }
        }
    )


class BaselineComparisonResponse(BaseModel):
    """Schema for baseline comparison response."""

    baseline: Dict[str, Any] = Field(..., description="Baseline summary info")
    comparison_date: datetime = Field(..., description="When comparison was performed")
    summary: ComparisonSummarySchema = Field(..., description="Summary statistics")
    task_variances: List[TaskVarianceSchema] = Field(..., description="Detailed task variances")
    new_tasks: List[Dict[str, Any]] = Field(..., description="Tasks added after baseline")
    deleted_tasks: List[Dict[str, Any]] = Field(..., description="Tasks deleted after baseline")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "baseline": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Initial Plan Q4 2025",
                    "created_at": "2025-10-17T14:30:00Z"
                },
                "comparison_date": "2025-10-20T16:45:00Z",
                "summary": {
                    "total_tasks": 100,
                    "tasks_ahead": 15,
                    "tasks_behind": 10,
                    "tasks_on_track": 75,
                    "avg_variance_days": -0.5,
                    "critical_path_variance_days": 3.0
                },
                "task_variances": [
                    {
                        "task_id": "abc-123",
                        "task_name": "Setup Infrastructure",
                        "variance_days": -2,
                        "is_ahead": True,
                        "is_behind": False,
                        "start_date_variance": -1,
                        "end_date_variance": -2,
                        "duration_variance": 0,
                        "status_changed": True,
                        "dependencies_changed": False
                    }
                ],
                "new_tasks": [
                    {
                        "task_id": "xyz-789",
                        "task_name": "Emergency Security Patch",
                        "added_after_baseline": True
                    }
                ],
                "deleted_tasks": [
                    {
                        "task_id": "old-456",
                        "task_name": "Deprecated Feature",
                        "existed_in_baseline": True
                    }
                ]
            }
        }
    )
