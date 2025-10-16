"""
Monte Carlo simulation engine for probabilistic project scheduling.

Orchestrates multiple simulation iterations using task duration sampling
and statistical analysis to provide confidence intervals and probability
distributions for project completion dates.
"""

from datetime import date
from typing import Callable, Dict, List, Optional, Set

import numpy as np
from pydantic import BaseModel, Field

from app.services.scheduler.scheduler_service import SchedulerService, TaskInput


class MonteCarloResult(BaseModel):
    """
    Results from Monte Carlo simulation with statistical analysis.

    Attributes:
        mean_duration: Average project duration across all iterations
        median_duration: Median (P50) project duration
        std_dev: Standard deviation of project durations
        percentiles: Dictionary of percentile values
            (e.g., {10: 45.2, 50: 52.0, 90: 61.5})
        iterations: Number of simulation iterations performed
        durations: List of all simulated project durations (in working days)
    """

    mean_duration: float = Field(
        ge=0.0, description="Mean project duration in working days"
    )
    median_duration: float = Field(ge=0.0, description="Median (P50) project duration")
    std_dev: float = Field(ge=0.0, description="Standard deviation of durations")
    percentiles: Dict[int, float] = Field(
        description="Percentile values (e.g., {10: 45.2, 50: 52.0, 90: 61.5})"
    )
    iterations: int = Field(gt=0, description="Number of iterations performed")
    durations: List[float] = Field(description="All simulated durations")

    class Config:
        json_schema_extra = {
            "example": {
                "mean_duration": 52.3,
                "median_duration": 51.5,
                "std_dev": 4.8,
                "percentiles": {10: 45.2, 50: 51.5, 90: 61.5, 95: 65.0, 99: 72.1},
                "iterations": 10000,
                "durations": [50.0, 51.2, 49.8],  # Truncated for example
            }
        }


class TaskDistributionInput(BaseModel):
    """
    Task specification with duration distribution for Monte Carlo simulation.

    For now, supports a sampler function. In the future, this will integrate
    with Phase B1 (distributions) and B2 (sampling).
    """

    task_id: str = Field(description="Unique task identifier")
    dependencies: str = Field(
        default="", description="Comma-separated dependency task IDs"
    )
    # For now, we'll accept a callable that returns sampled durations
    # This will be replaced with proper distribution objects in B1/B2 integration

    class Config:
        arbitrary_types_allowed = True


class MonteCarloEngine:
    """
    Monte Carlo simulation engine for probabilistic project scheduling.

    Runs multiple iterations of project scheduling with sampled task durations
    to generate statistical distributions of possible project completion times.

    Usage:
        engine = MonteCarloEngine(iterations=10000)
        result = engine.simulate(
            tasks=[
                TaskDistributionInput(task_id="T001", dependencies=""),
                TaskDistributionInput(task_id="T002", dependencies="T001"),
            ],
            duration_sampler=lambda task_id: {...},  # Returns sampled duration
            project_start=date(2025, 1, 13),
        )
    """

    def __init__(
        self,
        iterations: int = 10000,
        scheduler: Optional[SchedulerService] = None,
    ):
        """
        Initialize Monte Carlo engine.

        Args:
            iterations: Number of simulation iterations (default 10,000)
            scheduler: Optional SchedulerService instance (creates new if not provided)
        """
        if iterations <= 0:
            raise ValueError("Iterations must be positive")

        self.iterations = iterations
        self.scheduler = scheduler or SchedulerService()

    def simulate(
        self,
        tasks: List[TaskDistributionInput],
        duration_sampler: Callable[[str], float],
        project_start: date,
        holidays: Optional[List[date]] = None,
        workdays: Optional[Set[int]] = None,
        percentiles: Optional[List[int]] = None,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation for project scheduling.

        Args:
            tasks: List of tasks with distribution specifications
            duration_sampler: Function that takes task_id and returns
                sampled duration
            project_start: Project start date
            holidays: Optional list of holiday dates
            workdays: Optional set of working weekday numbers
            percentiles: List of percentile values to calculate
                (default: [10, 50, 90, 95, 99])

        Returns:
            MonteCarloResult with statistical analysis

        Raises:
            ValueError: If simulation fails or produces invalid results
        """
        if not tasks:
            raise ValueError("Task list cannot be empty")

        if percentiles is None:
            percentiles = [10, 50, 90, 95, 99]

        # Validate percentiles
        for p in percentiles:
            if not 0 <= p <= 100:
                raise ValueError(f"Percentile must be between 0 and 100, got {p}")

        # Storage for results
        durations: List[float] = []

        # Run iterations
        for iteration in range(self.iterations):
            try:
                # Step 1: Sample durations for this iteration
                sampled_tasks = []
                for task in tasks:
                    sampled_duration = duration_sampler(task.task_id)

                    # Validate sampled duration
                    if sampled_duration <= 0:
                        raise ValueError(
                            f"Iteration {iteration}: Sampled duration must be "
                            f"positive, got {sampled_duration} for "
                            f"task {task.task_id}"
                        )

                    sampled_tasks.append(
                        TaskInput(
                            task_id=task.task_id,
                            duration=sampled_duration,
                            dependencies=task.dependencies,
                        )
                    )

                # Step 2: Run scheduler with sampled durations
                schedule_result = self.scheduler.calculate_schedule(
                    tasks=sampled_tasks,
                    project_start=project_start,
                    holidays=holidays,
                    workdays=workdays,
                )

                # Step 3: Collect project duration
                durations.append(schedule_result.project_duration)

            except Exception as e:
                raise ValueError(
                    f"Simulation failed at iteration {iteration}: {e}"
                ) from e

        # Step 4: Calculate statistics
        durations_array = np.array(durations)

        # Calculate requested percentiles
        percentile_values = {}
        for p in percentiles:
            percentile_values[p] = float(np.percentile(durations_array, p))

        # Return results
        return MonteCarloResult(
            mean_duration=float(np.mean(durations_array)),
            median_duration=float(np.median(durations_array)),
            std_dev=float(np.std(durations_array)),
            percentiles=percentile_values,
            iterations=self.iterations,
            durations=durations,
        )
