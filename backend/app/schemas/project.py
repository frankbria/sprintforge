"""Pydantic schemas for Project API requests and responses."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.excel.config import ProjectFeatures, SprintConfig, WorkingDaysConfig


class ProjectConfigSchema(BaseModel):
    """Project configuration schema matching Excel ProjectConfig."""

    project_id: Optional[str] = Field(
        default=None,
        description="Project identifier (auto-generated if not provided)"
    )
    project_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Project name"
    )
    sprint_pattern: str = Field(
        default="YY.Q.#",
        description="Sprint numbering pattern (e.g., 'YY.Q.#', 'PI-N.Sprint-M')"
    )
    sprint_duration_weeks: int = Field(
        default=2,
        ge=1,
        le=8,
        description="Sprint duration in weeks"
    )
    working_days: List[int] = Field(
        default=[1, 2, 3, 4, 5],
        description="Working days as ISO weekday numbers (1=Monday, 7=Sunday)"
    )
    holidays: List[str] = Field(
        default_factory=list,
        description="List of holiday dates in ISO format (YYYY-MM-DD)"
    )
    hours_per_day: float = Field(
        default=8.0,
        ge=1.0,
        le=24.0,
        description="Working hours per day"
    )
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "monte_carlo": False,
            "critical_path": True,
            "gantt_chart": True,
            "earned_value": False,
            "resource_leveling": False,
            "burndown_chart": False,
            "sprint_tracking": False,
        },
        description="Feature flags for Excel generation"
    )

    @field_validator("working_days")
    @classmethod
    def validate_working_days(cls, v: List[int]) -> List[int]:
        """Validate working days are valid ISO weekday numbers."""
        if not v:
            raise ValueError("At least one working day must be specified")

        for day in v:
            if day < 1 or day > 7:
                raise ValueError(
                    f"Invalid weekday number: {day}. Must be 1-7 (Monday-Sunday)"
                )

        if len(v) != len(set(v)):
            raise ValueError("Duplicate working days found")

        return sorted(v)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_name": "My Agile Project",
                "sprint_pattern": "YY.Q.#",
                "sprint_duration_weeks": 2,
                "working_days": [1, 2, 3, 4, 5],
                "holidays": ["2025-01-01", "2025-12-25"],
                "hours_per_day": 8.0,
                "features": {
                    "monte_carlo": True,
                    "critical_path": True,
                    "gantt_chart": True,
                    "earned_value": True,
                    "sprint_tracking": True,
                    "burndown_chart": True,
                },
            }
        }
    )


class ProjectBase(BaseModel):
    """Base project schema with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Project name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Project description"
    )
    template_id: Optional[str] = Field(
        default="agile_basic",
        description="Excel template ID (e.g., 'agile_basic', 'waterfall_advanced')"
    )

    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    configuration: ProjectConfigSchema = Field(
        ...,
        description="Project configuration for Excel generation"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "My Agile Project",
                "description": "Sprint planning for Q1 2025",
                "template_id": "agile_advanced",
                "configuration": {
                    "project_name": "My Agile Project",
                    "sprint_pattern": "YY.Q.#",
                    "sprint_duration_weeks": 2,
                    "working_days": [1, 2, 3, 4, 5],
                    "holidays": ["2025-01-01", "2025-12-25"],
                    "features": {
                        "monte_carlo": True,
                        "critical_path": True,
                        "gantt_chart": True,
                        "earned_value": True,
                        "sprint_tracking": True,
                    },
                },
            }
        }
    )


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project (all fields optional)."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Project name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Project description"
    )
    template_id: Optional[str] = Field(
        default=None,
        description="Excel template ID"
    )
    configuration: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Project configuration (partial updates supported)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Project Name",
                "configuration": {
                    "sprint_duration_weeks": 3
                },
            }
        }
    )


class ProjectResponse(ProjectBase):
    """Schema for project API responses."""

    id: UUID = Field(..., description="Project UUID")
    owner_id: UUID = Field(..., description="Owner user ID")
    configuration: Dict[str, Any] = Field(
        ...,
        description="Project configuration"
    )
    template_version: str = Field(..., description="Template version")
    is_public: bool = Field(..., description="Public sharing enabled")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_generated_at: Optional[datetime] = Field(
        default=None,
        description="Last Excel generation timestamp"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "My Agile Project",
                "description": "Sprint planning for Q1 2025",
                "template_id": "agile_advanced",
                "owner_id": "650e8400-e29b-41d4-a716-446655440000",
                "configuration": {
                    "project_name": "My Agile Project",
                    "sprint_pattern": "YY.Q.#",
                    "features": {"monte_carlo": True, "critical_path": True},
                },
                "template_version": "1.0",
                "is_public": False,
                "created_at": "2025-02-03T10:00:00Z",
                "updated_at": "2025-02-03T10:00:00Z",
                "last_generated_at": None,
            }
        },
    )


class ProjectListResponse(BaseModel):
    """Schema for paginated project list responses."""

    total: int = Field(..., description="Total number of projects")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Pagination offset")
    projects: List[ProjectResponse] = Field(..., description="List of projects")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 42,
                "limit": 20,
                "offset": 0,
                "projects": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "My Agile Project",
                        "description": "Sprint planning for Q1 2025",
                        "template_id": "agile_advanced",
                        "owner_id": "650e8400-e29b-41d4-a716-446655440000",
                        "configuration": {"sprint_pattern": "YY.Q.#"},
                        "template_version": "1.0",
                        "is_public": False,
                        "created_at": "2025-02-03T10:00:00Z",
                        "updated_at": "2025-02-03T10:00:00Z",
                        "last_generated_at": "2025-02-03T11:30:00Z",
                    }
                ],
            }
        }
    )
