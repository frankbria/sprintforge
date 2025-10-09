"""
Project configuration models for Excel generation.

Provides Pydantic models for validating and managing project configuration,
including sprint patterns, working days, holidays, and feature flags.
"""

from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import structlog

logger = structlog.get_logger(__name__)


class SprintPatternType(str, Enum):
    """Supported sprint numbering pattern types."""

    YEAR_QUARTER_NUMBER = "YY.Q.#"  # e.g., "25.Q1.3"
    PI_SPRINT = "PI-N.Sprint-M"  # e.g., "PI-2.Sprint-4"
    CALENDAR_WEEK = "YYYY.WW"  # e.g., "2025.W15"
    CUSTOM = "CUSTOM"  # User-defined pattern


class FeatureFlag(str, Enum):
    """Available feature flags for Excel generation."""

    MONTE_CARLO = "monte_carlo"
    RESOURCE_LEVELING = "resource_leveling"
    EARNED_VALUE = "earned_value"
    CRITICAL_PATH = "critical_path"
    BASELINE_TRACKING = "baseline_tracking"
    BURNDOWN_CHARTS = "burndown_charts"
    CUSTOM_FORMULAS = "custom_formulas"


class WorkingDaysConfig(BaseModel):
    """Configuration for working days and business hours."""

    working_days: List[int] = Field(
        default=[1, 2, 3, 4, 5],
        description="Working days as ISO weekday numbers (1=Monday, 7=Sunday)"
    )
    holidays: List[date] = Field(
        default_factory=list,
        description="List of holiday dates to exclude from working days"
    )
    hours_per_day: float = Field(
        default=8.0,
        ge=1.0,
        le=24.0,
        description="Working hours per day"
    )

    @field_validator("working_days")
    @classmethod
    def validate_working_days(cls, v: List[int]) -> List[int]:
        """Validate working days are valid ISO weekday numbers."""
        if not v:
            raise ValueError("At least one working day must be specified")

        for day in v:
            if day < 1 or day > 7:
                raise ValueError(f"Invalid weekday number: {day}. Must be 1-7 (Monday-Sunday)")

        if len(v) != len(set(v)):
            raise ValueError("Duplicate working days found")

        return sorted(v)

    @field_validator("holidays")
    @classmethod
    def validate_holidays(cls, v: List[date]) -> List[date]:
        """Validate and sort holidays."""
        return sorted(set(v))  # Remove duplicates and sort


class SprintConfig(BaseModel):
    """Configuration for sprint pattern and numbering."""

    pattern_type: SprintPatternType = Field(
        default=SprintPatternType.YEAR_QUARTER_NUMBER,
        description="Type of sprint numbering pattern"
    )
    custom_pattern: Optional[str] = Field(
        default=None,
        description="Custom pattern string if pattern_type is CUSTOM"
    )
    duration_weeks: int = Field(
        default=2,
        ge=1,
        le=8,
        description="Sprint duration in weeks (1-8)"
    )
    start_date: Optional[date] = Field(
        default=None,
        description="First sprint start date for calculation"
    )

    @model_validator(mode="after")
    def validate_custom_pattern(self):
        """Validate custom pattern is provided when pattern_type is CUSTOM."""
        if self.pattern_type == SprintPatternType.CUSTOM and not self.custom_pattern:
            raise ValueError("custom_pattern must be provided when pattern_type is CUSTOM")
        return self


class ProjectFeatures(BaseModel):
    """Feature flags controlling Excel template capabilities."""

    monte_carlo: bool = Field(
        default=False,
        description="Enable Monte Carlo simulation formulas"
    )
    resource_leveling: bool = Field(
        default=False,
        description="Enable resource allocation and leveling"
    )
    earned_value: bool = Field(
        default=True,
        description="Enable Earned Value Management (EVM) formulas"
    )
    critical_path: bool = Field(
        default=True,
        description="Enable Critical Path Method (CPM) formulas"
    )
    baseline_tracking: bool = Field(
        default=False,
        description="Enable baseline comparison tracking"
    )
    burndown_charts: bool = Field(
        default=True,
        description="Enable burndown/burnup chart formulas"
    )
    custom_formulas: bool = Field(
        default=False,
        description="Allow user-defined custom formulas"
    )

    def get_enabled_features(self) -> List[str]:
        """Get list of enabled feature names."""
        return [
            field_name
            for field_name, value in self.model_dump().items()
            if value is True
        ]

    def is_enabled(self, feature: FeatureFlag) -> bool:
        """Check if a specific feature is enabled."""
        return getattr(self, feature.value, False)


class ProjectConfig(BaseModel):
    """
    Complete project configuration for Excel template generation.

    This Pydantic model validates and manages all configuration aspects
    for generating Excel templates, including project metadata, sprint
    patterns, working days, and feature flags.

    Example:
        >>> config = ProjectConfig(
        ...     project_id="proj_123",
        ...     project_name="My Project",
        ...     sprint_config=SprintConfig(
        ...         pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
        ...         duration_weeks=2
        ...     )
        ... )
    """

    project_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique project identifier"
    )
    project_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable project name"
    )
    sprint_config: SprintConfig = Field(
        default_factory=SprintConfig,
        description="Sprint pattern and numbering configuration"
    )
    working_days_config: WorkingDaysConfig = Field(
        default_factory=WorkingDaysConfig,
        description="Working days and holidays configuration"
    )
    features: ProjectFeatures = Field(
        default_factory=ProjectFeatures,
        description="Feature flags for Excel capabilities"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metadata"
    )

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate project ID format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("project_id must contain only alphanumeric characters, hyphens, and underscores")
        return v

    def get_sprint_pattern(self) -> str:
        """Get the sprint pattern string for display."""
        if self.sprint_config.pattern_type == SprintPatternType.CUSTOM:
            return self.sprint_config.custom_pattern or "CUSTOM"
        return self.sprint_config.pattern_type.value

    def get_working_days_list(self) -> List[int]:
        """Get sorted list of working days."""
        return self.working_days_config.working_days

    def get_holidays_list(self) -> List[date]:
        """Get sorted list of holidays."""
        return self.working_days_config.holidays

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Convert to legacy dictionary format for backward compatibility.

        This method maintains compatibility with the old ProjectConfig class
        that was used before Pydantic migration.
        """
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "sprint_pattern": self.get_sprint_pattern(),
            "features": self.features.model_dump(),
            "metadata": self.metadata,
            "working_days": self.working_days_config.working_days,
            "holidays": [h.isoformat() for h in self.working_days_config.holidays],
            "sprint_duration_weeks": self.sprint_config.duration_weeks,
        }

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "proj_2025_q1",
                    "project_name": "Q1 2025 Initiative",
                    "sprint_config": {
                        "pattern_type": "YY.Q.#",
                        "duration_weeks": 2,
                    },
                    "working_days_config": {
                        "working_days": [1, 2, 3, 4, 5],
                        "holidays": ["2025-01-01", "2025-07-04"],
                    },
                    "features": {
                        "critical_path": True,
                        "earned_value": True,
                        "monte_carlo": False,
                    },
                }
            ]
        }
    }
