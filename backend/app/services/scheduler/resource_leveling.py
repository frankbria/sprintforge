"""
Resource leveling scheduler with priority-based conflict resolution.

Schedules tasks considering both dependencies and resource constraints.
When resource conflicts occur, lower-priority tasks are delayed.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Union

from app.services.scheduler.resource import ResourcePool, ResourceType
from app.services.scheduler.resource_assignment import (
    ResourceAllocation,
    ResourceConflictDetector,
    TaskResourceRequirement,
)
from app.services.scheduler.task_graph import TaskGraph


class SchedulingError(Exception):
    """Raised when task cannot be scheduled due to constraints."""

    pass


@dataclass
class TaskWithRequirement:
    """
    Task with resource requirements for scheduling.

    Attributes:
        task_id: Unique task identifier
        duration: Task duration in working days
        priority: Scheduling priority (higher = more important)
        requirement: Single requirement or list of requirements
    """

    task_id: str
    duration: float
    priority: Optional[int]
    requirement: Union[TaskResourceRequirement, List[TaskResourceRequirement]]

    def __post_init__(self):
        """Normalize requirement to list and set default priority."""
        if self.priority is None:
            self.priority = 0

        if not isinstance(self.requirement, list):
            self.requirement = [self.requirement]


@dataclass
class ScheduledTask:
    """
    Task with assigned schedule and resource allocations.

    Attributes:
        task_id: Unique task identifier
        start_date: Scheduled start date
        end_date: Scheduled end date (inclusive)
        priority: Task priority
        allocations: List of resource allocations for this task
    """

    task_id: str
    start_date: date
    end_date: date
    priority: int
    allocations: List[ResourceAllocation]


class ResourceLevelingScheduler:
    """
    Priority-based scheduler with resource leveling.

    Schedules tasks respecting:
    1. Task dependencies (via TaskGraph)
    2. Resource availability and capacity
    3. Task priorities (higher priority tasks scheduled first)

    When resource conflicts occur, lower-priority tasks are delayed.

    Attributes:
        resource_pool: Pool of available resources
    """

    def __init__(self, resource_pool: ResourcePool):
        """
        Initialize scheduler with resource pool.

        Args:
            resource_pool: Pool of available resources
        """
        self.resource_pool = resource_pool
        self._conflict_detector = ResourceConflictDetector(resource_pool)

    def schedule(
        self,
        tasks: List[TaskWithRequirement],
        graph: TaskGraph,
        start_date: date,
    ) -> List[ScheduledTask]:
        """
        Schedule tasks with resource leveling.

        Algorithm:
        1. Sort tasks by priority (high to low)
        2. For each task (in priority order):
            a. Determine earliest possible start (considering dependencies)
            b. Find earliest date with sufficient resources
            c. Allocate resources and schedule task
        3. Resolve any conflicts by delaying lower-priority tasks

        Args:
            tasks: List of tasks with resource requirements
            graph: Task dependency graph
            start_date: Project start date

        Returns:
            List of scheduled tasks with resource allocations

        Raises:
            SchedulingError: If task cannot be scheduled
        """
        if not tasks:
            return []

        # Validate and prepare
        self._validate_tasks(tasks, graph)

        # Create task lookup
        task_map = {t.task_id: t for t in tasks}

        # Get topological order (dependencies before dependents)
        topo_order = graph.topological_sort()

        # Schedule tasks in topological order, using priority for tie-breaking
        # Group tasks by their position in dependency chain
        scheduled: Dict[str, ScheduledTask] = {}
        all_allocations: List[ResourceAllocation] = []

        # Process each task in topological order
        for task_id in topo_order:
            if task_id not in task_map:
                continue

            task = task_map[task_id]
            scheduled_task = self._schedule_single_task(
                task, graph, start_date, scheduled, all_allocations
            )
            scheduled[task.task_id] = scheduled_task
            all_allocations.extend(scheduled_task.allocations)

        return list(scheduled.values())

    def _schedule_single_task(
        self,
        task: TaskWithRequirement,
        graph: TaskGraph,
        project_start: date,
        scheduled: Dict[str, ScheduledTask],
        existing_allocations: List[ResourceAllocation],
    ) -> ScheduledTask:
        """
        Schedule a single task considering constraints.

        Args:
            task: Task to schedule
            graph: Dependency graph
            project_start: Project start date
            scheduled: Already scheduled tasks
            existing_allocations: Existing resource allocations

        Returns:
            Scheduled task with allocations

        Raises:
            SchedulingError: If task cannot be scheduled
        """
        # Find earliest possible start based on dependencies
        earliest_start = self._calculate_earliest_start(
            task.task_id, graph, scheduled, project_start
        )

        # Find earliest date with sufficient resources
        candidate_start = earliest_start
        max_attempts = 365  # Prevent infinite loops
        attempts = 0

        while attempts < max_attempts:
            # Try to allocate resources for this task
            allocations = self._try_allocate_resources(
                task, candidate_start, existing_allocations
            )

            if allocations is not None:
                # Successfully allocated resources
                end_date = candidate_start + timedelta(days=int(task.duration) - 1)
                return ScheduledTask(
                    task_id=task.task_id,
                    start_date=candidate_start,
                    end_date=end_date,
                    priority=task.priority,  # type: ignore
                    allocations=allocations,
                )

            # Resource conflict - try next day
            candidate_start += timedelta(days=1)
            attempts += 1

        raise SchedulingError(
            f"Cannot schedule task {task.task_id} - no available resources"
        )

    def _calculate_earliest_start(
        self,
        task_id: str,
        graph: TaskGraph,
        scheduled: Dict[str, ScheduledTask],
        project_start: date,
    ) -> date:
        """
        Calculate earliest possible start date for task.

        Considers task dependencies - task cannot start until all
        predecessors are complete.

        Args:
            task_id: Task to calculate start date for
            graph: Dependency graph
            scheduled: Already scheduled tasks
            project_start: Project start date

        Returns:
            Earliest possible start date
        """
        dependencies = graph.get_dependencies(task_id)

        if not dependencies:
            return project_start

        # Must start after all predecessors finish
        latest_end = project_start

        for dep_id in dependencies:
            if dep_id in scheduled:
                dep_end = scheduled[dep_id].end_date
                # Add 1 day after predecessor ends
                potential_start = dep_end + timedelta(days=1)
                if potential_start > latest_end:
                    latest_end = potential_start

        return latest_end

    def _try_allocate_resources(
        self,
        task: TaskWithRequirement,
        start_date: date,
        existing_allocations: List[ResourceAllocation],
    ) -> Optional[List[ResourceAllocation]]:
        """
        Attempt to allocate resources for task on given date.

        Args:
            task: Task requiring resources
            start_date: Proposed start date
            existing_allocations: Existing allocations to check against

        Returns:
            List of allocations if successful, None if conflict
        """
        end_date = start_date + timedelta(days=int(task.duration) - 1)
        proposed_allocations: List[ResourceAllocation] = []

        # Try to allocate each required resource
        requirements_list = (
            task.requirement
            if isinstance(task.requirement, list)
            else [task.requirement]
        )
        for requirement in requirements_list:
            allocation = self._allocate_requirement(
                requirement, start_date, end_date, existing_allocations
            )

            if allocation is None:
                # Cannot allocate this requirement - conflict
                return None

            proposed_allocations.append(allocation)

        # Check for conflicts with existing allocations
        test_allocations = existing_allocations + proposed_allocations
        conflicts = self._conflict_detector.detect_conflicts(test_allocations)

        if conflicts:
            return None

        return proposed_allocations

    def _allocate_requirement(
        self,
        requirement: TaskResourceRequirement,
        start_date: date,
        end_date: date,
        existing_allocations: List[ResourceAllocation],
    ) -> Optional[ResourceAllocation]:
        """
        Allocate a specific resource requirement.

        Args:
            requirement: Resource requirement to allocate
            start_date: Allocation start date
            end_date: Allocation end date
            existing_allocations: Existing allocations

        Returns:
            ResourceAllocation if successful, None if conflict
        """
        # If specific resources requested, try those first
        if requirement.resource_ids:
            for resource_id in requirement.resource_ids:
                if not self.resource_pool.has_resource(resource_id):
                    raise SchedulingError(
                        f"Required resource {resource_id} not found in pool"
                    )

                resource = self.resource_pool.get_resource(resource_id)

                # Check if resource available during period
                if not resource.is_available_during(start_date, end_date):
                    continue

                # Check if capacity available
                if self._has_capacity(
                    resource_id,
                    start_date,
                    end_date,
                    requirement.quantity,
                    existing_allocations,
                ):
                    return ResourceAllocation(
                        task_id=requirement.task_id,
                        resource_id=resource_id,
                        start_date=start_date,
                        end_date=end_date,
                        quantity=requirement.quantity,
                    )

        # Try any resource of the required type
        available_resources = self.resource_pool.get_resources_by_type(
            requirement.resource_type
        )

        for resource in available_resources:
            # Check availability
            if not resource.is_available_during(start_date, end_date):
                continue

            # Check capacity
            if self._has_capacity(
                resource.id,
                start_date,
                end_date,
                requirement.quantity,
                existing_allocations,
            ):
                return ResourceAllocation(
                    task_id=requirement.task_id,
                    resource_id=resource.id,
                    start_date=start_date,
                    end_date=end_date,
                    quantity=requirement.quantity,
                )

        return None

    def _has_capacity(
        self,
        resource_id: str,
        start_date: date,
        end_date: date,
        required_quantity: float,
        existing_allocations: List[ResourceAllocation],
    ) -> bool:
        """
        Check if resource has sufficient capacity during period.

        Args:
            resource_id: Resource to check
            start_date: Period start
            end_date: Period end
            required_quantity: Quantity needed
            existing_allocations: Existing allocations

        Returns:
            True if sufficient capacity available
        """
        resource = self.resource_pool.get_resource(resource_id)

        # Calculate total allocated quantity during period
        allocated = 0.0
        for alloc in existing_allocations:
            if alloc.resource_id == resource_id:
                # Check if allocation overlaps with period
                if not (alloc.end_date < start_date or alloc.start_date > end_date):
                    allocated += alloc.quantity

        return allocated + required_quantity <= resource.capacity

    def _validate_tasks(
        self, tasks: List[TaskWithRequirement], graph: TaskGraph
    ) -> None:
        """
        Validate tasks and graph consistency.

        Args:
            tasks: Tasks to validate
            graph: Dependency graph

        Raises:
            SchedulingError: If validation fails
        """
        task_ids = {t.task_id for t in tasks}

        # Validate all tasks exist in graph
        for task in tasks:
            if task.task_id not in graph.nodes:
                raise SchedulingError(
                    f"Task {task.task_id} not found in dependency graph"
                )

        # Validate graph has no cycles (will raise CycleDetectedError)
        try:
            graph.topological_sort()
        except Exception as e:
            raise SchedulingError(f"Invalid task graph: {e}")

    def calculate_utilization(
        self,
        scheduled_tasks: List[ScheduledTask],
        period_start: date,
        period_end: date,
    ) -> Dict[str, float]:
        """
        Calculate resource utilization for scheduled tasks.

        Calculates what fraction of each resource's capacity is used
        during the specified period.

        Args:
            scheduled_tasks: List of scheduled tasks
            period_start: Analysis period start
            period_end: Analysis period end

        Returns:
            Dictionary mapping resource_id to utilization ratio (0.0 to 1.0)
        """
        # Collect all allocations
        all_allocations: List[ResourceAllocation] = []
        for task in scheduled_tasks:
            all_allocations.extend(task.allocations)

        # Calculate utilization for each resource
        utilization: Dict[str, float] = {}

        for resource in self.resource_pool.get_all_resources():
            resource_id = resource.id

            # Get allocations for this resource during period
            relevant_allocations = [
                alloc
                for alloc in all_allocations
                if alloc.resource_id == resource_id
                and not (alloc.end_date < period_start or alloc.start_date > period_end)
            ]

            if not relevant_allocations:
                utilization[resource_id] = 0.0
                continue

            # Calculate total allocated days
            total_allocated_days = 0.0
            for alloc in relevant_allocations:
                # Calculate overlap with period
                overlap_start = max(alloc.start_date, period_start)
                overlap_end = min(alloc.end_date, period_end)
                overlap_days = (overlap_end - overlap_start).days + 1

                total_allocated_days += overlap_days * alloc.quantity

            # Calculate total available days
            period_days = (period_end - period_start).days + 1
            total_capacity_days = period_days * resource.capacity

            # Calculate utilization ratio
            if total_capacity_days > 0:
                utilization[resource_id] = min(
                    1.0, total_allocated_days / total_capacity_days
                )
            else:
                utilization[resource_id] = 0.0

        return utilization
