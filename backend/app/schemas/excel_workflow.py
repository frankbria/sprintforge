"""Pydantic schemas for Excel workflow API endpoints."""

from datetime import date, datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class ExcelSimulationResponse(BaseModel):
    """Response from Excel upload & simulation endpoint."""

    simulation_id: int = Field(..., description="Unique simulation result ID")
    project_id: str = Field(..., description="Project UUID")
    project_duration_days: float = Field(
        ..., ge=0, description="Mean project duration in working days"
    )
    confidence_intervals: Dict[int, float] = Field(
        ..., description="Confidence intervals mapping percentile to duration"
    )
    mean_duration: float = Field(
        ..., ge=0, description="Mean duration across all iterations"
    )
    median_duration: float = Field(
        ..., ge=0, description="Median (P50) project duration"
    )
    iterations_run: int = Field(..., gt=0, description="Number of iterations executed")
    task_count: int = Field(..., ge=0, description="Number of tasks in simulation")
    download_url: str = Field(
        ..., description="URL to download Excel file with results"
    )
    created_at: datetime = Field(..., description="Timestamp when simulation completed")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "simulation_id": 123,
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "project_duration_days": 52.3,
                "confidence_intervals": {
                    10: 45.2,
                    50: 51.5,
                    90: 61.5,
                    95: 65.0,
                    99: 72.1,
                },
                "mean_duration": 52.3,
                "median_duration": 51.5,
                "iterations_run": 10000,
                "task_count": 15,
                "download_url": "/api/v1/simulations/123/excel",
                "created_at": "2025-01-15T10:30:00Z",
            }
        }


class ExcelValidationError(BaseModel):
    """Excel file validation error details."""

    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Human-readable error message")
    row: Optional[int] = Field(None, description="Row number where error occurred")
    column: Optional[str] = Field(None, description="Column name where error occurred")

    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "invalid_format",
                "message": "Missing required column: task_name",
                "row": None,
                "column": "task_name",
            }
        }


class ExcelTemplateRequest(BaseModel):
    """Request parameters for Excel template download."""

    include_sample_data: bool = Field(
        default=False, description="Include sample data in template"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "include_sample_data": True,
            }
        }


class ParsedTask(BaseModel):
    """Task parsed from Excel file."""

    task_id: str = Field(..., description="Unique task identifier")
    task_name: str = Field(..., description="Task name/description")
    optimistic: float = Field(..., ge=0, description="Optimistic duration estimate")
    most_likely: float = Field(..., ge=0, description="Most likely duration estimate")
    pessimistic: float = Field(..., ge=0, description="Pessimistic duration estimate")
    dependencies: str = Field(
        default="", description="Comma-separated list of dependency task IDs"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "TASK-1",
                "task_name": "Setup development environment",
                "optimistic": 1.0,
                "most_likely": 3.0,
                "pessimistic": 5.0,
                "dependencies": "",
            }
        }
