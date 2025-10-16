"""
Scheduler service module for project scheduling and Monte Carlo simulation.

This module provides:
- TaskGraph: Directed acyclic graph for task dependencies
- CPM: Critical Path Method calculations
- WorkCalendar: Holiday and weekend handling
- MonteCarloEngine: Probabilistic schedule simulation
"""

from app.services.scheduler.task_graph import TaskGraph, CycleDetectedError
from app.services.scheduler.cpm import (
    calculate_forward_pass,
    calculate_backward_pass,
    calculate_critical_path,
)
from app.services.scheduler.models import TaskScheduleData, CriticalPathResult
from app.services.scheduler.work_calendar import WorkCalendar, calculate_task_dates
from app.services.scheduler.dependency_parser import parse_dependencies, DependencyParseError
from app.services.scheduler.scheduler_service import (
    SchedulerService,
    SchedulerError,
    TaskInput,
    ScheduleResult,
)
from app.services.scheduler.monte_carlo import (
    MonteCarloEngine,
    MonteCarloResult,
    TaskDistributionInput,
)

__all__ = [
    "TaskGraph",
    "CycleDetectedError",
    "calculate_forward_pass",
    "calculate_backward_pass",
    "calculate_critical_path",
    "TaskScheduleData",
    "CriticalPathResult",
    "WorkCalendar",
    "calculate_task_dates",
    "parse_dependencies",
    "DependencyParseError",
    "SchedulerService",
    "SchedulerError",
    "TaskInput",
    "ScheduleResult",
    "MonteCarloEngine",
    "MonteCarloResult",
    "TaskDistributionInput",
]
