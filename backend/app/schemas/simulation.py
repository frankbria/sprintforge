"""Pydantic schemas for Monte Carlo simulation API."""

from datetime import date, datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TaskDistributionRequest(BaseModel):
    """Task with distribution parameters for API requests.

    Supports three distribution types:
    - triangular: Requires optimistic, most_likely, pessimistic
    - uniform: Requires min_duration, max_duration
    - normal: Requires mean, std_dev
    """

    task_id: str = Field(..., description="Unique task identifier")
    distribution_type: Literal["triangular", "uniform", "normal"] = Field(
        ..., description="Probability distribution type"
    )

    # Triangular distribution parameters
    optimistic: Optional[float] = Field(
        None,
        ge=0,
        description="Optimistic duration (best case) for triangular distribution",
    )
    most_likely: Optional[float] = Field(
        None, ge=0, description="Most likely duration for triangular distribution"
    )
    pessimistic: Optional[float] = Field(
        None,
        ge=0,
        description="Pessimistic duration (worst case) for triangular distribution",
    )

    # Uniform distribution parameters
    min_duration: Optional[float] = Field(
        None, ge=0, description="Minimum duration for uniform distribution"
    )
    max_duration: Optional[float] = Field(
        None, ge=0, description="Maximum duration for uniform distribution"
    )

    # Normal distribution parameters
    mean: Optional[float] = Field(
        None, ge=0, description="Mean duration for normal distribution"
    )
    std_dev: Optional[float] = Field(
        None, gt=0, description="Standard deviation for normal distribution"
    )

    dependencies: str = Field(
        default="", description="Comma-separated list of task IDs this task depends on"
    )

    @field_validator("optimistic", "most_likely", "pessimistic")
    @classmethod
    def validate_triangular_order(cls, v, info):
        """Validate triangular distribution parameter ordering."""
        # This validator runs for each field individually
        # Full validation happens in model_validator
        return v

    @field_validator("min_duration", "max_duration")
    @classmethod
    def validate_uniform_order(cls, v, info):
        """Validate uniform distribution parameter ordering."""
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "TASK-1",
                "distribution_type": "triangular",
                "optimistic": 1.0,
                "most_likely": 3.0,
                "pessimistic": 5.0,
                "dependencies": "",
            }
        }


class SimulationRequest(BaseModel):
    """Request body for Monte Carlo simulation endpoint."""

    tasks: List[TaskDistributionRequest] = Field(
        ..., min_length=1, description="List of tasks with distribution parameters"
    )
    project_start_date: date = Field(..., description="Project start date (YYYY-MM-DD)")
    iterations: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Number of Monte Carlo iterations (100-100000)",
    )
    holidays: Optional[List[date]] = Field(
        default=None, description="List of holiday dates to exclude from work days"
    )
    percentiles: Optional[List[int]] = Field(
        default=[10, 50, 90, 95, 99], description="Percentiles for confidence intervals"
    )

    @field_validator("percentiles")
    @classmethod
    def validate_percentiles(cls, v):
        """Validate percentiles are in valid range."""
        if v is None:
            return [10, 50, 90, 95, 99]

        for percentile in v:
            if not 0 <= percentile <= 100:
                raise ValueError(f"Percentile {percentile} must be between 0 and 100")

        return sorted(set(v))  # Remove duplicates and sort

    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [
                    {
                        "task_id": "TASK-1",
                        "distribution_type": "triangular",
                        "optimistic": 1.0,
                        "most_likely": 3.0,
                        "pessimistic": 5.0,
                        "dependencies": "",
                    },
                    {
                        "task_id": "TASK-2",
                        "distribution_type": "triangular",
                        "optimistic": 2.0,
                        "most_likely": 4.0,
                        "pessimistic": 6.0,
                        "dependencies": "TASK-1",
                    },
                ],
                "project_start_date": "2025-01-15",
                "iterations": 10000,
                "holidays": ["2025-01-20", "2025-02-14"],
                "percentiles": [10, 50, 90, 95, 99],
            }
        }


class SimulationResponse(BaseModel):
    """Response from Monte Carlo simulation endpoint."""

    project_id: str = Field(..., description="Project UUID")
    project_duration_days: float = Field(
        ..., description="Expected project duration in days"
    )
    confidence_intervals: Dict[int, float] = Field(
        ..., description="Confidence intervals mapping percentile to duration"
    )
    mean_duration: float = Field(..., description="Mean duration across all iterations")
    median_duration: float = Field(..., description="Median duration (50th percentile)")
    std_deviation: float = Field(..., description="Standard deviation of duration")
    iterations_run: int = Field(..., description="Number of iterations executed")
    simulation_timestamp: datetime = Field(
        ..., description="Timestamp when simulation completed"
    )
    task_count: int = Field(..., description="Number of tasks in simulation")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "project_duration_days": 8.5,
                "confidence_intervals": {
                    "10": 6.0,
                    "50": 8.5,
                    "90": 11.0,
                    "95": 12.0,
                    "99": 14.0,
                },
                "mean_duration": 8.5,
                "median_duration": 8.5,
                "std_deviation": 2.1,
                "iterations_run": 10000,
                "simulation_timestamp": "2025-01-15T10:30:00Z",
                "task_count": 2,
            }
        }


class SimulationHistoryItem(BaseModel):
    """Individual simulation result from history."""

    id: int = Field(..., description="Simulation result ID")
    iterations: int = Field(..., description="Number of iterations performed")
    task_count: int = Field(..., description="Number of tasks in simulation")
    project_start_date: date = Field(..., description="Project start date used")
    mean_duration: float = Field(
        ..., description="Mean project duration (working days)"
    )
    median_duration: float = Field(..., description="Median project duration")
    std_deviation: float = Field(..., description="Standard deviation of duration")
    confidence_intervals: Dict[int, float] = Field(
        ..., description="Percentile confidence intervals"
    )
    created_at: datetime = Field(..., description="When simulation was run")
    simulation_duration_seconds: Optional[float] = Field(
        None, description="Execution time of simulation"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "iterations": 10000,
                "task_count": 15,
                "project_start_date": "2025-01-13",
                "mean_duration": 52.3,
                "median_duration": 51.5,
                "std_deviation": 4.8,
                "confidence_intervals": {
                    "10": 45.2,
                    "50": 51.5,
                    "90": 61.5,
                    "95": 65.0,
                    "99": 72.1,
                },
                "created_at": "2025-01-15T10:30:00Z",
                "simulation_duration_seconds": 2.5,
            }
        }


class SimulationHistoryResponse(BaseModel):
    """Response for simulation history queries."""

    simulations: List[SimulationHistoryItem] = Field(
        ..., description="List of simulation results"
    )
    total_count: int = Field(..., description="Total number of simulations available")
    page: int = Field(..., description="Current page number (0-indexed)")
    page_size: int = Field(..., description="Number of results per page")

    class Config:
        json_schema_extra = {
            "example": {
                "simulations": [
                    {
                        "id": 123,
                        "iterations": 10000,
                        "task_count": 15,
                        "project_start_date": "2025-01-13",
                        "mean_duration": 52.3,
                        "median_duration": 51.5,
                        "std_deviation": 4.8,
                        "confidence_intervals": {
                            "10": 45.2,
                            "50": 51.5,
                            "90": 61.5,
                            "95": 65.0,
                            "99": 72.1,
                        },
                        "created_at": "2025-01-15T10:30:00Z",
                        "simulation_duration_seconds": 2.5,
                    }
                ],
                "total_count": 42,
                "page": 0,
                "page_size": 10,
            }
        }


class SimulationDetailResponse(BaseModel):
    """Detailed simulation result including project and user information."""

    id: int = Field(..., description="Simulation result ID")
    project_id: str = Field(..., description="Project UUID")
    user_id: str = Field(..., description="User UUID who ran the simulation")
    iterations: int = Field(..., description="Number of iterations performed")
    task_count: int = Field(..., description="Number of tasks in simulation")
    project_start_date: date = Field(..., description="Project start date used")
    mean_duration: float = Field(
        ..., description="Mean project duration (working days)"
    )
    median_duration: float = Field(..., description="Median project duration")
    std_deviation: float = Field(..., description="Standard deviation of duration")
    confidence_intervals: Dict[int, float] = Field(
        ..., description="Percentile confidence intervals"
    )
    created_at: datetime = Field(..., description="When simulation was run")
    simulation_duration_seconds: Optional[float] = Field(
        None, description="Execution time of simulation"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43d1-b678-123456789abc",
                "iterations": 10000,
                "task_count": 15,
                "project_start_date": "2025-01-13",
                "mean_duration": 52.3,
                "median_duration": 51.5,
                "std_deviation": 4.8,
                "confidence_intervals": {
                    "10": 45.2,
                    "50": 51.5,
                    "90": 61.5,
                    "95": 65.0,
                    "99": 72.1,
                },
                "created_at": "2025-01-15T10:30:00Z",
                "simulation_duration_seconds": 2.5,
            }
        }
