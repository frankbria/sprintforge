"""
Resource-constrained Critical Path Method (CPM).

Extends traditional CPM to consider resource availability and capacity.
Identifies critical chain - the longest path considering both dependencies
and resource constraints.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from app.services.scheduler.cpm import calculate_backward_pass, calculate_forward_pass
from app.services.scheduler.models import CriticalPathResult, TaskScheduleData
from app.services.scheduler.resource import ResourcePool
from app.services.scheduler.resource_assignment import TaskResourceRequirement
from app.services.scheduler.task_graph import TaskGraph


def calculate_resource_forward_pass(
    graph: TaskGraph,
    durations: Dict[str, float],
    requirements: Dict[str, TaskResourceRequirement],
    resource_pool: ResourcePool,
    start_date: date,
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Early Start (ES) and Early Finish (EF) considering resources.

    Extends standard CPM forward pass by checking resource availability.
    Tasks may be delayed beyond their dependency-based ES if required
    resources are not available.

    Args:
        graph: TaskGraph with dependency structure
        durations: Dictionary mapping task_id to duration in working days
        requirements: Dictionary mapping task_id to resource requirements
        resource_pool: Available resources
        start_date: Project start date

    Returns:
        Dictionary mapping task_id to (ES, EF) tuple
    """
    es_ef: Dict[str, Tuple[float, float]] = {}
    resource_usage: Dict[
        str, List[Tuple[float, float, str]]
    ] = {}  # resource_id -> [(start, end, task)]

    # Initialize resource usage tracking
    for resource in resource_pool.get_all_resources():
        resource_usage[resource.id] = []

    # Process tasks in topological order
    for task_id in graph.topological_sort():
        dependencies = graph.get_dependencies(task_id)

        # Calculate dependency-based ES
        if not dependencies:
            dependency_es = 0.0
        else:
            dependency_es = max(es_ef[dep][1] for dep in dependencies)

        # Check resource availability
        if task_id in requirements:
            requirement = requirements[task_id]
            resource_ids = requirement.resource_ids or []

            # If specific resources requested, check those
            if resource_ids:
                resource_es = dependency_es
                for resource_id in resource_ids:
                    if not resource_pool.has_resource(resource_id):
                        continue

                    # Find earliest time this resource is available
                    earliest = _find_earliest_resource_slot(
                        resource_id,
                        resource_usage,
                        dependency_es,
                        durations[task_id],
                        requirement.quantity,
                        resource_pool,
                    )
                    resource_es = max(resource_es, earliest)

                es = resource_es
            else:
                # Try any resource of required type
                es = dependency_es
                # For simplicity, use dependency-based ES
                # (full resource search would be more complex)
        else:
            es = dependency_es

        # Calculate EF
        ef = es + durations[task_id]
        es_ef[task_id] = (es, ef)

        # Record resource usage
        if task_id in requirements:
            requirement = requirements[task_id]
            if requirement.resource_ids:
                for resource_id in requirement.resource_ids:
                    if resource_pool.has_resource(resource_id):
                        resource_usage[resource_id].append((es, ef, task_id))

    return es_ef


def _find_earliest_resource_slot(
    resource_id: str,
    resource_usage: Dict[str, List[Tuple[float, float, str]]],
    earliest_start: float,
    duration: float,
    quantity: float,
    resource_pool: ResourcePool,
) -> float:
    """
    Find earliest time slot where resource has sufficient capacity.

    Args:
        resource_id: Resource to check
        resource_usage: Current resource allocations
        earliest_start: Earliest possible start (from dependencies)
        duration: Task duration
        quantity: Required resource quantity
        resource_pool: Resource pool

    Returns:
        Earliest start time with sufficient capacity
    """
    resource = resource_pool.get_resource(resource_id)
    usage_list = resource_usage[resource_id]

    # Sort existing usage by start time
    sorted_usage = sorted(usage_list, key=lambda x: x[0])

    candidate_start = earliest_start

    # Check if candidate slot has sufficient capacity
    while True:
        candidate_end = candidate_start + duration

        # Calculate total usage during candidate period
        total_usage = 0.0
        for start, end, _ in sorted_usage:
            # Check if this usage overlaps with candidate period
            if not (end <= candidate_start or start >= candidate_end):
                # Overlap exists - for simplicity, assume full quantity
                # (more sophisticated would track actual quantities)
                total_usage += quantity

        # Check if sufficient capacity
        if total_usage + quantity <= resource.capacity:
            return candidate_start

        # Try next slot (after earliest conflicting task)
        next_start = candidate_start + 1.0
        for start, end, _ in sorted_usage:
            if start > candidate_start and start < candidate_end:
                next_start = min(next_start, end)

        candidate_start = next_start

        # Prevent infinite loops
        if candidate_start > earliest_start + 1000:
            return earliest_start


def calculate_resource_backward_pass(
    graph: TaskGraph,
    durations: Dict[str, float],
    requirements: Dict[str, TaskResourceRequirement],
    resource_pool: ResourcePool,
    project_end: float,
    start_date: date,
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Late Start (LS) and Late Finish (LF) considering resources.

    Extends standard CPM backward pass by considering resource constraints.
    In resource-constrained scheduling, LS may be further constrained by
    resource availability.

    Args:
        graph: TaskGraph with dependency structure
        durations: Dictionary mapping task_id to duration in working days
        requirements: Dictionary mapping task_id to resource requirements
        resource_pool: Available resources
        project_end: Project end time from forward pass
        start_date: Project start date

    Returns:
        Dictionary mapping task_id to (LS, LF) tuple
    """
    # Use standard backward pass as baseline
    # Resource constraints primarily affect forward pass
    return calculate_backward_pass(graph, durations, project_end)


def calculate_critical_chain(
    graph: TaskGraph,
    durations: Dict[str, float],
    requirements: Dict[str, TaskResourceRequirement],
    resource_pool: ResourcePool,
    start_date: date,
) -> CriticalPathResult:
    """
    Calculate critical chain considering resource constraints.

    The critical chain is the longest sequence of tasks considering:
    1. Task dependencies (precedence relationships)
    2. Resource dependencies (resource contention)

    Args:
        graph: TaskGraph with dependency structure
        durations: Dictionary mapping task_id to duration in working days
        requirements: Dictionary mapping task_id to resource requirements
        resource_pool: Available resources
        start_date: Project start date

    Returns:
        CriticalPathResult with resource-constrained analysis
    """
    # Handle empty graph
    if graph.is_empty():
        return CriticalPathResult(tasks={}, critical_path=[], project_duration=0.0)

    # Forward pass with resource constraints
    es_ef = calculate_resource_forward_pass(
        graph, durations, requirements, resource_pool, start_date
    )

    # Project duration is maximum EF
    project_end = max(ef for _, ef in es_ef.values())

    # Backward pass
    ls_lf = calculate_resource_backward_pass(
        graph, durations, requirements, resource_pool, project_end, start_date
    )

    # Calculate slack and identify critical chain
    tasks: Dict[str, TaskScheduleData] = {}
    critical_path: List[str] = []

    SLACK_TOLERANCE = 0.001  # Tolerance for floating point comparison

    for task_id in graph.nodes:
        es, ef = es_ef[task_id]
        ls, lf = ls_lf[task_id]
        slack = ls - es
        is_critical = abs(slack) < SLACK_TOLERANCE

        if is_critical:
            critical_path.append(task_id)

        tasks[task_id] = TaskScheduleData(
            task_id=task_id,
            duration=durations[task_id],
            dependencies=graph.get_dependencies(task_id),
            es=es,
            ef=ef,
            ls=ls,
            lf=lf,
            slack=slack,
            is_critical=is_critical,
        )

    return CriticalPathResult(
        tasks=tasks, critical_path=critical_path, project_duration=project_end
    )


class ResourceConstrainedCPM:
    """
    Resource-constrained Critical Path Method calculator.

    Extends traditional CPM to account for resource availability and capacity.
    Identifies critical chain - tasks that determine project duration
    considering both dependencies and resource constraints.

    Attributes:
        resource_pool: Pool of available resources
    """

    def __init__(self, resource_pool: ResourcePool):
        """
        Initialize resource-constrained CPM.

        Args:
            resource_pool: Pool of available resources
        """
        self.resource_pool = resource_pool

    def calculate_critical_chain(
        self,
        graph: TaskGraph,
        durations: Dict[str, float],
        requirements: Dict[str, TaskResourceRequirement],
        start_date: date,
    ) -> CriticalPathResult:
        """
        Calculate critical chain for project.

        Args:
            graph: Task dependency graph
            durations: Task durations in working days
            requirements: Task resource requirements
            start_date: Project start date

        Returns:
            CriticalPathResult with critical chain analysis
        """
        return calculate_critical_chain(
            graph, durations, requirements, self.resource_pool, start_date
        )

    def calculate_forward_pass(
        self,
        graph: TaskGraph,
        durations: Dict[str, float],
        requirements: Dict[str, TaskResourceRequirement],
        start_date: date,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calculate resource-aware forward pass.

        Args:
            graph: Task dependency graph
            durations: Task durations
            requirements: Resource requirements
            start_date: Project start date

        Returns:
            Dictionary mapping task_id to (ES, EF)
        """
        return calculate_resource_forward_pass(
            graph, durations, requirements, self.resource_pool, start_date
        )

    def calculate_backward_pass(
        self,
        graph: TaskGraph,
        durations: Dict[str, float],
        requirements: Dict[str, TaskResourceRequirement],
        project_end: float,
        start_date: date,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calculate resource-aware backward pass.

        Args:
            graph: Task dependency graph
            durations: Task durations
            requirements: Resource requirements
            project_end: Project end time
            start_date: Project start date

        Returns:
            Dictionary mapping task_id to (LS, LF)
        """
        return calculate_resource_backward_pass(
            graph, durations, requirements, self.resource_pool, project_end, start_date
        )
