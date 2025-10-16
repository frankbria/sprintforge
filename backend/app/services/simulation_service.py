"""
SimulationService - Business logic layer for Monte Carlo simulations.

Orchestrates Monte Carlo simulation execution with validation, error handling,
and result formatting for API consumption.
"""

from datetime import date, datetime
from typing import Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.services.scheduler.monte_carlo import MonteCarloEngine, TaskDistributionInput
from app.services.scheduler.scheduler_service import SchedulerError


class SimulationError(Exception):
    """Raised when simulation fails due to invalid input or execution errors."""

    pass


class SimulationResult(BaseModel):
    """
    Formatted simulation results for API response.

    Attributes:
        project_duration_days: Mean project duration in working days
        confidence_intervals: Dictionary mapping percentiles to duration values
        mean_duration: Average project duration across iterations
        median_duration: Median (P50) project duration
        std_deviation: Standard deviation of project durations
        iterations_run: Number of simulation iterations performed
        simulation_date: Timestamp when simulation was executed
        task_count: Number of tasks in the project
    """

    project_duration_days: float = Field(
        ge=0.0, description="Mean project duration in working days"
    )
    confidence_intervals: Dict[int, float] = Field(
        description="Percentile values (e.g., {10: 45.2, 50: 52.0, 90: 61.5})"
    )
    mean_duration: float = Field(
        ge=0.0, description="Mean project duration across iterations"
    )
    median_duration: float = Field(ge=0.0, description="Median (P50) project duration")
    std_deviation: float = Field(ge=0.0, description="Standard deviation of durations")
    iterations_run: int = Field(gt=0, description="Number of iterations performed")
    simulation_date: datetime = Field(description="Timestamp of simulation execution")
    task_count: int = Field(ge=0, description="Number of tasks in project")

    class Config:
        json_schema_extra = {
            "example": {
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
                "std_deviation": 4.8,
                "iterations_run": 10000,
                "simulation_date": "2025-01-13T10:30:00",
                "task_count": 15,
            }
        }


class SimulationService:
    """
    Business logic service for Monte Carlo project scheduling simulations.

    Orchestrates simulation execution with input validation, error handling,
    and result formatting. Uses MonteCarloEngine for core simulation logic.

    Usage:
        service = SimulationService()
        result = service.run_simulation(
            tasks=[...],
            project_start=date(2025, 1, 13),
            iterations=10000,
            duration_sampler=lambda task_id: sample_duration(task_id),
        )
    """

    def __init__(self, default_iterations: int = 10000):
        """
        Initialize simulation service.

        Args:
            default_iterations: Default number of iterations if not specified
        """
        self.default_iterations = default_iterations

    def run_simulation(
        self,
        tasks: List[TaskDistributionInput],
        project_start: date,
        duration_sampler: Callable[[str], float],
        iterations: Optional[int] = None,
        holidays: Optional[List[date]] = None,
        workdays: Optional[Set[int]] = None,
        percentiles: Optional[List[int]] = None,
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation and return formatted results.

        Args:
            tasks: List of tasks with distribution specifications
            project_start: Project start date
            duration_sampler: Function that takes task_id and returns sampled duration
            iterations: Number of simulation iterations (default: 10,000)
            holidays: Optional list of holiday dates
            workdays: Optional set of working weekday numbers (0=Mon, 6=Sun)
            percentiles: List of percentile values to calculate
                (default: [10, 50, 90, 95, 99])

        Returns:
            SimulationResult with formatted statistics and metadata

        Raises:
            ValueError: If input validation fails
            SimulationError: If simulation execution fails
        """
        # Use default iterations if not specified
        if iterations is None:
            iterations = self.default_iterations

        # Use default percentiles if not specified
        if percentiles is None:
            percentiles = [10, 50, 90, 95, 99]

        # Step 1: Validate inputs
        self.validate_simulation_input(tasks=tasks, iterations=iterations)
        self._validate_percentiles(percentiles=percentiles)

        # Step 2: Run Monte Carlo simulation
        try:
            engine = MonteCarloEngine(iterations=iterations)
            monte_carlo_result = engine.simulate(
                tasks=tasks,
                duration_sampler=duration_sampler,
                project_start=project_start,
                holidays=holidays,
                workdays=workdays,
                percentiles=percentiles,
            )
        except SchedulerError as e:
            # Wrap scheduler errors as simulation errors
            raise SimulationError(f"Scheduling failed: {e}") from e
        except ValueError as e:
            # Handle errors from engine (e.g., negative durations, cycles)
            error_msg = str(e)
            if "Sampled duration must be positive" in error_msg:
                raise SimulationError(error_msg) from e
            elif "circular dependency" in error_msg.lower():
                raise SimulationError(f"Circular dependency detected: {e}") from e
            elif "Unknown dependency" in error_msg:
                raise SimulationError(error_msg) from e
            else:
                raise SimulationError(f"Simulation execution failed: {e}") from e
        except Exception as e:
            # Catch any other unexpected errors
            raise SimulationError(f"Unexpected simulation error: {e}") from e

        # Step 3: Format and return results
        return SimulationResult(
            project_duration_days=monte_carlo_result.mean_duration,
            confidence_intervals=monte_carlo_result.percentiles,
            mean_duration=monte_carlo_result.mean_duration,
            median_duration=monte_carlo_result.median_duration,
            std_deviation=monte_carlo_result.std_dev,
            iterations_run=monte_carlo_result.iterations,
            simulation_date=datetime.now(),
            task_count=len(tasks),
        )

    def validate_simulation_input(
        self, tasks: List[TaskDistributionInput], iterations: int
    ) -> None:
        """
        Validate simulation parameters.

        Args:
            tasks: List of tasks to validate
            iterations: Number of iterations to validate

        Raises:
            ValueError: If validation fails with descriptive message
        """
        # Validate task list
        if not tasks:
            raise ValueError("Task list cannot be empty")

        # Validate iterations range
        if iterations < 100 or iterations > 100000:
            raise ValueError(
                f"Iterations must be between 100 and 100000, got {iterations}"
            )

    def _validate_percentiles(self, percentiles: List[int]) -> None:
        """
        Validate percentile values.

        Args:
            percentiles: List of percentiles to validate

        Raises:
            ValueError: If any percentile is invalid
        """
        for p in percentiles:
            if not 0 <= p <= 100:
                raise ValueError(f"Percentiles must be between 0 and 100, got {p}")
