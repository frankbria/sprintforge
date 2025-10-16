"""
Critical Path Method (CPM) implementation.

Provides forward pass, backward pass, and critical path identification
for project scheduling using the Critical Path Method.
"""

from typing import Dict, Tuple
from app.services.scheduler.task_graph import TaskGraph
from app.services.scheduler.models import TaskScheduleData, CriticalPathResult


def calculate_forward_pass(
    graph: TaskGraph, durations: Dict[str, float]
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Early Start (ES) and Early Finish (EF) for all tasks.

    Uses forward pass algorithm:
    - For tasks with no dependencies: ES = 0
    - For tasks with dependencies: ES = max(EF of all predecessors)
    - EF = ES + duration

    Args:
        graph: TaskGraph with dependency structure
        durations: Dictionary mapping task_id to duration in working days

    Returns:
        Dictionary mapping task_id to (ES, EF) tuple
    """
    es_ef: Dict[str, Tuple[float, float]] = {}

    # Process tasks in topological order (dependencies before dependents)
    for task_id in graph.topological_sort():
        dependencies = graph.get_dependencies(task_id)

        if not dependencies:
            # Root task - starts at time 0
            es = 0.0
        else:
            # Task starts after all predecessors finish
            es = max(es_ef[dep][1] for dep in dependencies)

        ef = es + durations[task_id]
        es_ef[task_id] = (es, ef)

    return es_ef


def calculate_backward_pass(
    graph: TaskGraph, durations: Dict[str, float], project_end: float
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Late Start (LS) and Late Finish (LF) for all tasks.

    Uses backward pass algorithm:
    - For leaf tasks (no successors): LF = project_end
    - For tasks with successors: LF = min(LS of all successors)
    - LS = LF - duration

    Args:
        graph: TaskGraph with dependency structure
        durations: Dictionary mapping task_id to duration in working days
        project_end: Project end time from forward pass

    Returns:
        Dictionary mapping task_id to (LS, LF) tuple
    """
    ls_lf: Dict[str, Tuple[float, float]] = {}

    # Process tasks in reverse topological order (dependents before dependencies)
    for task_id in reversed(graph.topological_sort()):
        successors = graph.get_successors(task_id)

        if not successors:
            # Leaf task - must finish by project end
            lf = project_end
        else:
            # Task must finish before earliest start of any successor
            lf = min(ls_lf[succ][0] for succ in successors)

        ls = lf - durations[task_id]
        ls_lf[task_id] = (ls, lf)

    return ls_lf


def calculate_critical_path(
    graph: TaskGraph, durations: Dict[str, float]
) -> CriticalPathResult:
    """
    Calculate complete CPM analysis including critical path.

    Performs:
    1. Forward pass (ES, EF calculation)
    2. Backward pass (LS, LF calculation)
    3. Slack calculation (LS - ES)
    4. Critical path identification (tasks with zero slack)

    Args:
        graph: TaskGraph with dependency structure
        durations: Dictionary mapping task_id to duration in working days

    Returns:
        CriticalPathResult with complete CPM analysis
    """
    # Handle empty graph
    if graph.is_empty():
        return CriticalPathResult(
            tasks={}, critical_path=[], project_duration=0.0
        )

    # Forward pass: Calculate ES and EF
    es_ef = calculate_forward_pass(graph, durations)

    # Project duration is the maximum EF
    project_end = max(ef for _, ef in es_ef.values())

    # Backward pass: Calculate LS and LF
    ls_lf = calculate_backward_pass(graph, durations, project_end)

    # Calculate slack and identify critical path
    tasks: Dict[str, TaskScheduleData] = {}
    critical_path: list[str] = []

    # Tolerance for floating point comparison (0.001 days = ~1 minute)
    SLACK_TOLERANCE = 0.001

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
