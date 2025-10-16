"""
Risk Analyzer - Monte Carlo risk integration for project scheduling.

Integrates Monte Carlo simulation with CPM to provide probabilistic risk analysis:
- Task criticality indices (% times task is on critical path)
- Probabilistic critical path identification
- Risk driver identification (high criticality + high variance)
- Completion confidence intervals
"""

from datetime import date, timedelta
from typing import Callable, Dict, List, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator

from app.services.scheduler.monte_carlo import MonteCarloEngine, TaskDistributionInput
from app.services.scheduler.scheduler_service import SchedulerService, TaskInput


class TaskCriticalityData(BaseModel):
    """
    Criticality analysis data for a single task.

    Attributes:
        task_id: Unique task identifier
        criticality_index: Percentage of iterations task was on critical path (0.0-1.0)
        times_critical: Number of iterations task was on critical path
        total_iterations: Total Monte Carlo iterations performed
        mean_duration: Average sampled duration across all iterations
        duration_variance: Variance of sampled durations
        is_risk_driver: True if task has high criticality AND high variance
    """

    task_id: str
    criticality_index: float = Field(
        ge=0.0, le=1.0, description="Criticality index (0.0 to 1.0)"
    )
    times_critical: int = Field(ge=0, description="Times task was critical")
    total_iterations: int = Field(gt=0, description="Total iterations")
    mean_duration: float = Field(ge=0.0, description="Mean task duration")
    duration_variance: float = Field(ge=0.0, description="Duration variance")
    is_risk_driver: bool = Field(description="High criticality + high variance")

    @field_validator("times_critical")
    @classmethod
    def validate_times_critical(cls, v: int, info) -> int:
        """Validate times_critical doesn't exceed total_iterations."""
        if "total_iterations" in info.data:
            if v > info.data["total_iterations"]:
                raise ValueError(
                    f"times_critical ({v}) cannot exceed total_iterations "
                    f"({info.data['total_iterations']})"
                )
        return v


class RiskMetrics(BaseModel):
    """
    Complete risk analysis results from Monte Carlo simulation.

    Attributes:
        probabilistic_critical_path: Task IDs ordered by criticality
            (highest first)
        task_criticality: Criticality data for each task
        risk_drivers: Task IDs with high criticality and high variance
        confidence_intervals: Completion dates by confidence level
            (e.g., {50: date, 75: date, 90: date})
    """

    probabilistic_critical_path: List[str] = Field(
        description="Tasks ordered by criticality"
    )
    task_criticality: Dict[str, TaskCriticalityData] = Field(
        description="Criticality data per task"
    )
    risk_drivers: List[str] = Field(description="High risk tasks")
    confidence_intervals: Dict[int, date] = Field(
        description="Completion dates by percentile"
    )


class RiskAnalyzer:
    """
    Risk analyzer integrating Monte Carlo simulation with CPM.

    Runs multiple simulation iterations, tracking which tasks appear on the
    critical path in each iteration, then calculates probabilistic risk metrics.

    Usage:
        analyzer = RiskAnalyzer()
        metrics = analyzer.analyze_risk(
            tasks=[
                TaskDistributionInput(task_id="T001", dependencies=""),
                TaskDistributionInput(task_id="T002", dependencies="T001"),
            ],
            duration_sampler=lambda task_id: sample_duration(task_id),
            project_start=date(2025, 1, 13),
            num_iterations=1000,
        )
    """

    def __init__(
        self,
        monte_carlo_engine: Optional[MonteCarloEngine] = None,
        scheduler: Optional[SchedulerService] = None,
    ):
        """
        Initialize RiskAnalyzer.

        Args:
            monte_carlo_engine: Optional MonteCarloEngine (creates default if None)
            scheduler: Optional SchedulerService (creates default if None)
        """
        self.monte_carlo_engine = monte_carlo_engine or MonteCarloEngine()
        self.scheduler = scheduler or SchedulerService()

    def analyze_risk(
        self,
        tasks: List[TaskDistributionInput],
        duration_sampler: Callable[[str], float],
        project_start: date,
        num_iterations: int = 1000,
        criticality_threshold: float = 0.5,
        variance_threshold: float = 1.0,
    ) -> RiskMetrics:
        """
        Perform complete risk analysis using Monte Carlo simulation.

        Args:
            tasks: List of tasks with distribution specifications
            duration_sampler: Function that returns sampled duration for task_id
            project_start: Project start date
            num_iterations: Number of Monte Carlo iterations
            criticality_threshold: Minimum criticality for risk drivers (default 0.5)
            variance_threshold: Minimum variance for risk drivers (default 1.0)

        Returns:
            RiskMetrics with complete risk analysis

        Raises:
            ValueError: If task list is empty or iterations invalid
        """
        if not tasks:
            raise ValueError("Task list cannot be empty")

        if num_iterations <= 0:
            raise ValueError(f"Iterations must be positive, got {num_iterations}")

        # Storage for tracking
        critical_path_counts: Dict[str, int] = {task.task_id: 0 for task in tasks}
        task_durations: Dict[str, List[float]] = {task.task_id: [] for task in tasks}
        completion_dates: List[date] = []

        # Run Monte Carlo iterations
        for iteration in range(num_iterations):
            # Step 1: Sample durations for this iteration
            sampled_tasks = []
            for task in tasks:
                sampled_duration = duration_sampler(task.task_id)

                # Store duration for variance calculation
                task_durations[task.task_id].append(sampled_duration)

                sampled_tasks.append(
                    TaskInput(
                        task_id=task.task_id,
                        duration=sampled_duration,
                        dependencies=task.dependencies,
                    )
                )

            # Step 2: Run CPM with sampled durations
            schedule_result = self.scheduler.calculate_schedule(
                tasks=sampled_tasks,
                project_start=project_start,
            )

            # Step 3: Track which tasks are on critical path
            for task_id in schedule_result.critical_path:
                critical_path_counts[task_id] += 1

            # Step 4: Calculate completion date
            max_duration = schedule_result.project_duration
            completion_date = project_start + timedelta(days=int(max_duration))
            completion_dates.append(completion_date)

        # Calculate criticality indices
        task_criticality_data = self._build_criticality_data(
            critical_path_counts=critical_path_counts,
            task_durations=task_durations,
            total_iterations=num_iterations,
            criticality_threshold=criticality_threshold,
            variance_threshold=variance_threshold,
        )

        # Identify probabilistic critical path (ordered by criticality)
        probabilistic_critical_path = self._identify_probabilistic_critical_path(
            task_criticality_data
        )

        # Identify risk drivers
        risk_drivers = self._identify_risk_drivers(task_criticality_data)

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(completion_dates)

        return RiskMetrics(
            probabilistic_critical_path=probabilistic_critical_path,
            task_criticality=task_criticality_data,
            risk_drivers=risk_drivers,
            confidence_intervals=confidence_intervals,
        )

    def _build_criticality_data(
        self,
        critical_path_counts: Dict[str, int],
        task_durations: Dict[str, List[float]],
        total_iterations: int,
        criticality_threshold: float,
        variance_threshold: float,
    ) -> Dict[str, TaskCriticalityData]:
        """
        Build TaskCriticalityData for each task.

        Args:
            critical_path_counts: Times each task was critical
            task_durations: Sampled durations for each task
            total_iterations: Total iterations performed
            criticality_threshold: Threshold for risk driver criticality
            variance_threshold: Threshold for risk driver variance

        Returns:
            Dictionary mapping task_id to TaskCriticalityData
        """
        task_criticality: Dict[str, TaskCriticalityData] = {}

        for task_id, times_critical in critical_path_counts.items():
            # Calculate criticality index
            criticality_index = times_critical / total_iterations

            # Calculate duration statistics
            durations = np.array(task_durations[task_id])
            mean_duration = float(np.mean(durations))
            duration_variance = float(np.var(durations))

            # Determine if task is a risk driver
            is_risk_driver = (
                criticality_index >= criticality_threshold
                and duration_variance >= variance_threshold
            )

            task_criticality[task_id] = TaskCriticalityData(
                task_id=task_id,
                criticality_index=criticality_index,
                times_critical=times_critical,
                total_iterations=total_iterations,
                mean_duration=mean_duration,
                duration_variance=duration_variance,
                is_risk_driver=is_risk_driver,
            )

        return task_criticality

    def _identify_probabilistic_critical_path(
        self, task_criticality: Dict[str, TaskCriticalityData]
    ) -> List[str]:
        """
        Identify probabilistic critical path (tasks ordered by criticality).

        Args:
            task_criticality: Criticality data for all tasks

        Returns:
            List of task IDs ordered by criticality index (highest first)
        """
        # Sort tasks by criticality index (descending)
        sorted_tasks = sorted(
            task_criticality.items(),
            key=lambda x: x[1].criticality_index,
            reverse=True,
        )

        return [task_id for task_id, _ in sorted_tasks]

    def _identify_risk_drivers(
        self, task_criticality: Dict[str, TaskCriticalityData]
    ) -> List[str]:
        """
        Identify risk drivers (high criticality + high variance tasks).

        Args:
            task_criticality: Criticality data for all tasks

        Returns:
            List of task IDs that are risk drivers
        """
        risk_drivers = [
            task_id for task_id, data in task_criticality.items() if data.is_risk_driver
        ]

        # Sort by criticality index for consistent ordering
        risk_drivers.sort(
            key=lambda tid: task_criticality[tid].criticality_index, reverse=True
        )

        return risk_drivers

    def _calculate_confidence_intervals(
        self, completion_dates: List[date]
    ) -> Dict[int, date]:
        """
        Calculate completion date confidence intervals.

        Args:
            completion_dates: List of completion dates from all iterations

        Returns:
            Dictionary mapping percentile to completion date
        """
        # Convert dates to ordinal numbers for percentile calculation
        date_ordinals = np.array([d.toordinal() for d in completion_dates])

        # Calculate standard percentiles
        percentiles = [50, 75, 90]
        confidence_intervals = {}

        for p in percentiles:
            ordinal = np.percentile(date_ordinals, p)
            confidence_intervals[p] = date.fromordinal(int(ordinal))

        return confidence_intervals
