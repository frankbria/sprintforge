"""
SchedulerService - Complete project scheduling orchestration.

Integrates TaskGraph, CPM, WorkCalendar, and dependency parsing to provide
end-to-end project scheduling functionality.
"""

from typing import List, Dict, Tuple, Optional, Set
from datetime import date
from pydantic import BaseModel, Field

from app.services.scheduler.task_graph import TaskGraph, CycleDetectedError
from app.services.scheduler.cpm import calculate_critical_path
from app.services.scheduler.work_calendar import WorkCalendar, calculate_task_dates
from app.services.scheduler.dependency_parser import parse_dependencies, DependencyParseError
from app.services.scheduler.models import TaskScheduleData, CriticalPathResult


class SchedulerError(Exception):
    """Raised when scheduling fails due to invalid input or constraints."""

    pass


class TaskInput(BaseModel):
    """Input specification for a task to be scheduled."""

    task_id: str = Field(description="Unique task identifier")
    duration: float = Field(gt=0.0, description="Task duration in working days (must be > 0)")
    dependencies: str = Field(default="", description="Comma-separated list of dependency task IDs")


class ScheduleResult(BaseModel):
    """Complete schedule calculation result."""

    tasks: Dict[str, TaskScheduleData] = Field(description="CPM data for each task")
    critical_path: List[str] = Field(description="Task IDs on critical path, in order")
    project_duration: float = Field(ge=0.0, description="Total project duration in working days")
    task_dates: Dict[str, Tuple[date, date]] = Field(
        description="Calendar dates for each task (start_date, end_date)"
    )

    class Config:
        arbitrary_types_allowed = True


class SchedulerService:
    """
    Complete project scheduling service.

    Orchestrates TaskGraph construction, CPM calculation, and calendar date
    conversion to provide end-to-end project scheduling.

    Usage:
        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=[
                TaskInput(task_id="T001", duration=5.0, dependencies=""),
                TaskInput(task_id="T002", duration=3.0, dependencies="T001"),
            ],
            project_start=date(2025, 1, 13),
        )
    """

    def calculate_schedule(
        self,
        tasks: List[TaskInput],
        project_start: date,
        holidays: Optional[List[date]] = None,
        workdays: Optional[Set[int]] = None,
    ) -> ScheduleResult:
        """
        Calculate complete project schedule with CPM and calendar dates.

        Args:
            tasks: List of tasks to schedule
            project_start: Project start date
            holidays: Optional list of holiday dates (non-working days)
            workdays: Optional set of working weekday numbers (0=Mon, 6=Sun)
                     Default is {0,1,2,3,4} for Monday-Friday

        Returns:
            ScheduleResult with CPM analysis and calendar dates

        Raises:
            SchedulerError: If scheduling fails due to invalid input or constraints
        """
        # Handle empty task list
        if not tasks:
            return ScheduleResult(
                tasks={},
                critical_path=[],
                project_duration=0.0,
                task_dates={},
            )

        try:
            # Step 1: Validate unique task IDs
            task_ids = [task.task_id for task in tasks]
            if len(task_ids) != len(set(task_ids)):
                duplicates = [tid for tid in task_ids if task_ids.count(tid) > 1]
                raise SchedulerError(
                    f"Duplicate task ID found: {', '.join(set(duplicates))}"
                )

            # Step 2: Parse dependencies and validate references
            task_dependencies: Dict[str, List[str]] = {}
            for task in tasks:
                try:
                    deps = parse_dependencies(task.dependencies)
                    task_dependencies[task.task_id] = deps

                    # Validate that all dependencies exist
                    for dep in deps:
                        if dep not in task_ids:
                            raise SchedulerError(
                                f"Unknown dependency '{dep}' referenced by task '{task.task_id}'"
                            )
                except DependencyParseError as e:
                    raise SchedulerError(f"Invalid dependency format for task '{task.task_id}': {e}")

            # Step 3: Build TaskGraph
            graph = TaskGraph()
            durations: Dict[str, float] = {}

            # First, add all nodes
            for task in tasks:
                graph.add_node(task.task_id, duration=task.duration)
                durations[task.task_id] = task.duration

            # Then, add all edges (now all nodes exist)
            for task in tasks:
                for dep in task_dependencies[task.task_id]:
                    graph.add_edge(dep, task.task_id)

            # Step 4: Calculate CPM (this validates no cycles)
            try:
                cpm_result = calculate_critical_path(graph, durations)
            except CycleDetectedError as e:
                raise SchedulerError(f"Circular dependency detected: {e}")

            # Step 5: Create WorkCalendar and calculate dates
            calendar = WorkCalendar(holidays=holidays, workdays=workdays)
            task_dates = calculate_task_dates(cpm_result, project_start, calendar)

            # Step 6: Return complete result
            return ScheduleResult(
                tasks=cpm_result.tasks,
                critical_path=cpm_result.critical_path,
                project_duration=cpm_result.project_duration,
                task_dates=task_dates,
            )

        except (SchedulerError, CycleDetectedError, DependencyParseError):
            # Re-raise known scheduler errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise SchedulerError(f"Unexpected scheduling error: {e}") from e
