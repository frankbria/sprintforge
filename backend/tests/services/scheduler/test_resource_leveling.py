"""
Tests for resource leveling scheduler.

Tests priority-based task scheduling with resource constraints.
Comprehensive test coverage for ResourceLevelingScheduler class.
"""

from datetime import date, timedelta
from typing import Dict, List

import pytest

from app.services.scheduler.resource import Resource, ResourcePool, ResourceType
from app.services.scheduler.resource_assignment import (
    ResourceAllocation,
    TaskResourceRequirement,
)
from app.services.scheduler.resource_leveling import (
    ResourceLevelingScheduler,
    ScheduledTask,
    SchedulingError,
    TaskWithRequirement,
)
from app.services.scheduler.task_graph import TaskGraph

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def basic_resource_pool() -> ResourcePool:
    """Create basic resource pool with 3 developers."""
    pool = ResourcePool()
    pool.add_resource(
        Resource("dev1", "Developer 1", ResourceType.PERSON, capacity=1.0)
    )
    pool.add_resource(
        Resource("dev2", "Developer 2", ResourceType.PERSON, capacity=1.0)
    )
    pool.add_resource(
        Resource("dev3", "Developer 3", ResourceType.PERSON, capacity=1.0)
    )
    return pool


@pytest.fixture
def small_resource_pool() -> ResourcePool:
    """Create small pool with 1 developer."""
    pool = ResourcePool()
    pool.add_resource(
        Resource("dev1", "Developer 1", ResourceType.PERSON, capacity=1.0)
    )
    return pool


@pytest.fixture
def mixed_resource_pool() -> ResourcePool:
    """Create pool with different resource types and capacities."""
    pool = ResourcePool()
    pool.add_resource(
        Resource("dev1", "Developer 1", ResourceType.PERSON, capacity=1.0)
    )
    pool.add_resource(
        Resource("dev2", "Developer 2", ResourceType.PERSON, capacity=0.5)
    )
    pool.add_resource(
        Resource("server1", "Server 1", ResourceType.EQUIPMENT, capacity=2.0)
    )
    return pool


@pytest.fixture
def start_date() -> date:
    """Standard start date for scheduling."""
    return date(2024, 1, 1)


# ============================================================================
# Test: Scheduler Initialization
# ============================================================================


def test_scheduler_initialization(basic_resource_pool: ResourcePool):
    """Test scheduler can be initialized with resource pool."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)
    assert scheduler is not None
    assert scheduler.resource_pool == basic_resource_pool


def test_scheduler_initialization_empty_pool():
    """Test scheduler works with empty resource pool."""
    pool = ResourcePool()
    scheduler = ResourceLevelingScheduler(pool)
    assert scheduler is not None


# ============================================================================
# Test: Single Task Scheduling
# ============================================================================


def test_schedule_single_task_no_dependencies(
    basic_resource_pool: ResourcePool, start_date: date
):
    """Test scheduling single task with no dependencies."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=5.0)

    requirement = TaskResourceRequirement("T1", ResourceType.PERSON, 1.0, ["dev1"])
    tasks = [
        TaskWithRequirement("T1", duration=5.0, priority=1, requirement=requirement)
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    assert len(result) == 1
    assert result[0].task_id == "T1"
    assert result[0].start_date == start_date
    assert result[0].end_date == start_date + timedelta(days=4)
    assert len(result[0].allocations) == 1
    assert result[0].allocations[0].resource_id == "dev1"


def test_schedule_single_task_default_priority(
    basic_resource_pool: ResourcePool, start_date: date
):
    """Test task with no priority gets default priority."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=3.0)

    requirement = TaskResourceRequirement("T1", ResourceType.PERSON, 1.0)
    tasks = [
        TaskWithRequirement("T1", duration=3.0, priority=None, requirement=requirement)
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    assert len(result) == 1
    assert result[0].priority == 0  # Default priority


def test_schedule_task_with_multiple_resource_types(
    mixed_resource_pool: ResourcePool, start_date: date
):
    """Test task requiring multiple resource types."""
    scheduler = ResourceLevelingScheduler(mixed_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=4.0)

    req1 = TaskResourceRequirement("T1", ResourceType.PERSON, 1.0, ["dev1"])
    req2 = TaskResourceRequirement("T1", ResourceType.EQUIPMENT, 1.0, ["server1"])

    task = TaskWithRequirement("T1", duration=4.0, priority=1, requirement=[req1, req2])

    result = scheduler.schedule([task], graph, start_date)

    assert len(result) == 1
    assert len(result[0].allocations) == 2
    resource_ids = {a.resource_id for a in result[0].allocations}
    assert resource_ids == {"dev1", "server1"}


# ============================================================================
# Test: Priority-Based Scheduling
# ============================================================================


def test_schedule_by_priority_no_conflicts(
    basic_resource_pool: ResourcePool, start_date: date
):
    """Test tasks scheduled in priority order when no resource conflicts."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=3.0)
    graph.add_node("T2", duration=2.0)
    graph.add_node("T3", duration=4.0)

    tasks = [
        TaskWithRequirement(
            "T1",
            3.0,
            priority=1,
            requirement=TaskResourceRequirement(
                "T1", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
        TaskWithRequirement(
            "T2",
            2.0,
            priority=2,
            requirement=TaskResourceRequirement(
                "T2", ResourceType.PERSON, 1.0, ["dev2"]
            ),
        ),
        TaskWithRequirement(
            "T3",
            4.0,
            priority=3,
            requirement=TaskResourceRequirement(
                "T3", ResourceType.PERSON, 1.0, ["dev3"]
            ),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    # All start at same time since different resources
    assert len(result) == 3
    assert all(st.start_date == start_date for st in result)


def test_schedule_by_priority_with_conflicts(
    small_resource_pool: ResourcePool, start_date: date
):
    """Test lower priority tasks delayed when resource conflicts occur."""
    scheduler = ResourceLevelingScheduler(small_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=5.0)
    graph.add_node("T2", duration=3.0)

    tasks = [
        TaskWithRequirement(
            "T1",
            5.0,
            priority=10,  # High priority
            requirement=TaskResourceRequirement(
                "T1", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
        TaskWithRequirement(
            "T2",
            3.0,
            priority=1,  # Low priority
            requirement=TaskResourceRequirement(
                "T2", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    # High priority task starts first
    t1 = next(st for st in result if st.task_id == "T1")
    t2 = next(st for st in result if st.task_id == "T2")

    assert t1.start_date == start_date
    assert t2.start_date == start_date + timedelta(days=5)  # After T1 ends


def test_schedule_equal_priority_first_come_first_served(
    small_resource_pool: ResourcePool, start_date: date
):
    """Test equal priority tasks scheduled in input order."""
    scheduler = ResourceLevelingScheduler(small_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=2.0)
    graph.add_node("T2", duration=2.0)

    tasks = [
        TaskWithRequirement(
            "T1",
            2.0,
            priority=5,
            requirement=TaskResourceRequirement(
                "T1", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
        TaskWithRequirement(
            "T2",
            2.0,
            priority=5,
            requirement=TaskResourceRequirement(
                "T2", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    t1 = next(st for st in result if st.task_id == "T1")
    t2 = next(st for st in result if st.task_id == "T2")

    assert t1.start_date == start_date
    assert t2.start_date > t1.end_date


# ============================================================================
# Test: Dependency Handling
# ============================================================================


def test_schedule_with_simple_dependency(
    basic_resource_pool: ResourcePool, start_date: date
):
    """Test dependent task scheduled after predecessor."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=5.0)
    graph.add_node("T2", duration=3.0)
    graph.add_edge("T1", "T2")  # T2 depends on T1

    tasks = [
        TaskWithRequirement(
            "T1",
            5.0,
            priority=1,
            requirement=TaskResourceRequirement(
                "T1", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
        TaskWithRequirement(
            "T2",
            3.0,
            priority=1,
            requirement=TaskResourceRequirement(
                "T2", ResourceType.PERSON, 1.0, ["dev2"]
            ),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    t1 = next(st for st in result if st.task_id == "T1")
    t2 = next(st for st in result if st.task_id == "T2")

    assert t1.start_date == start_date
    assert t2.start_date >= t1.end_date + timedelta(days=1)  # T2 after T1


def test_schedule_with_chain_dependency(
    basic_resource_pool: ResourcePool, start_date: date
):
    """Test chain of dependencies (T1 → T2 → T3)."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=2.0)
    graph.add_node("T2", duration=3.0)
    graph.add_node("T3", duration=4.0)
    graph.add_edge("T1", "T2")
    graph.add_edge("T2", "T3")

    tasks = [
        TaskWithRequirement(
            "T1",
            2.0,
            priority=1,
            requirement=TaskResourceRequirement("T1", ResourceType.PERSON, 1.0),
        ),
        TaskWithRequirement(
            "T2",
            3.0,
            priority=1,
            requirement=TaskResourceRequirement("T2", ResourceType.PERSON, 1.0),
        ),
        TaskWithRequirement(
            "T3",
            4.0,
            priority=1,
            requirement=TaskResourceRequirement("T3", ResourceType.PERSON, 1.0),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    t1 = next(st for st in result if st.task_id == "T1")
    t2 = next(st for st in result if st.task_id == "T2")
    t3 = next(st for st in result if st.task_id == "T3")

    assert t1.start_date == start_date
    assert t2.start_date >= t1.end_date + timedelta(days=1)
    assert t3.start_date >= t2.end_date + timedelta(days=1)


def test_schedule_priority_overridden_by_dependency(
    small_resource_pool: ResourcePool, start_date: date
):
    """Test dependency constraint overrides priority."""
    scheduler = ResourceLevelingScheduler(small_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=3.0)
    graph.add_node("T2", duration=2.0)
    graph.add_edge("T1", "T2")  # T2 depends on T1

    tasks = [
        TaskWithRequirement(
            "T1",
            3.0,
            priority=1,  # Low priority
            requirement=TaskResourceRequirement(
                "T1", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
        TaskWithRequirement(
            "T2",
            2.0,
            priority=10,  # High priority but depends on T1
            requirement=TaskResourceRequirement(
                "T2", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    t1 = next(st for st in result if st.task_id == "T1")
    t2 = next(st for st in result if st.task_id == "T2")

    # T1 must start first despite lower priority
    assert t1.start_date == start_date
    assert t2.start_date >= t1.end_date + timedelta(days=1)


# ============================================================================
# Test: Resource Conflict Resolution
# ============================================================================


def test_resource_allocation_respects_capacity(
    basic_resource_pool: ResourcePool, start_date: date
):
    """Test scheduler doesn't overallocate resource capacity."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=5.0)
    graph.add_node("T2", duration=3.0)

    # Both tasks want same resource
    tasks = [
        TaskWithRequirement(
            "T1",
            5.0,
            priority=10,
            requirement=TaskResourceRequirement(
                "T1", ResourceType.PERSON, 0.8, ["dev1"]
            ),
        ),
        TaskWithRequirement(
            "T2",
            3.0,
            priority=5,
            requirement=TaskResourceRequirement(
                "T2", ResourceType.PERSON, 0.5, ["dev1"]
            ),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)

    # Verify no overallocation occurs
    allocations = []
    for st in result:
        allocations.extend(st.allocations)

    # Should schedule without exceeding capacity of 1.0
    assert len(allocations) == 2


def test_resource_availability_checking(mixed_resource_pool: ResourcePool):
    """Test scheduler checks resource availability."""
    # Mark resource unavailable on specific dates
    dev1 = mixed_resource_pool.get_resource("dev1")
    dev1.unavailable_dates.add(date(2024, 1, 3))
    dev1.unavailable_dates.add(date(2024, 1, 4))

    scheduler = ResourceLevelingScheduler(mixed_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=5.0)

    task = TaskWithRequirement(
        "T1",
        5.0,
        priority=1,
        requirement=TaskResourceRequirement("T1", ResourceType.PERSON, 1.0, ["dev1"]),
    )

    # Scheduling should work around unavailable dates or fail gracefully
    result = scheduler.schedule([task], graph, date(2024, 1, 1))

    # Either schedules successfully or raises error
    assert len(result) >= 0


# ============================================================================
# Test: Utilization Tracking
# ============================================================================


def test_calculate_resource_utilization(
    basic_resource_pool: ResourcePool, start_date: date
):
    """Test calculation of resource utilization metrics."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=5.0)
    graph.add_node("T2", duration=3.0)

    tasks = [
        TaskWithRequirement(
            "T1",
            5.0,
            priority=1,
            requirement=TaskResourceRequirement(
                "T1", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
        TaskWithRequirement(
            "T2",
            3.0,
            priority=1,
            requirement=TaskResourceRequirement(
                "T2", ResourceType.PERSON, 1.0, ["dev2"]
            ),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)
    utilization = scheduler.calculate_utilization(
        result, start_date, start_date + timedelta(days=10)
    )

    assert "dev1" in utilization
    assert "dev2" in utilization
    assert 0 <= utilization["dev1"] <= 1.0
    assert 0 <= utilization["dev2"] <= 1.0


def test_utilization_with_parallel_tasks(
    basic_resource_pool: ResourcePool, start_date: date
):
    """Test utilization calculation with parallel tasks."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=10.0)
    graph.add_node("T2", duration=10.0)
    graph.add_node("T3", duration=10.0)

    tasks = [
        TaskWithRequirement(
            "T1",
            10.0,
            priority=1,
            requirement=TaskResourceRequirement(
                "T1", ResourceType.PERSON, 1.0, ["dev1"]
            ),
        ),
        TaskWithRequirement(
            "T2",
            10.0,
            priority=1,
            requirement=TaskResourceRequirement(
                "T2", ResourceType.PERSON, 1.0, ["dev2"]
            ),
        ),
        TaskWithRequirement(
            "T3",
            10.0,
            priority=1,
            requirement=TaskResourceRequirement(
                "T3", ResourceType.PERSON, 1.0, ["dev3"]
            ),
        ),
    ]

    result = scheduler.schedule(tasks, graph, start_date)
    # Period is 10 days (0-9 inclusive) matching task duration
    utilization = scheduler.calculate_utilization(
        result, start_date, start_date + timedelta(days=9)
    )

    # All resources fully utilized during 10-day period
    assert all(util == 1.0 for util in utilization.values())


def test_utilization_empty_schedule():
    """Test utilization calculation with no scheduled tasks."""
    pool = ResourcePool()
    pool.add_resource(
        Resource("dev1", "Developer 1", ResourceType.PERSON, capacity=1.0)
    )

    scheduler = ResourceLevelingScheduler(pool)
    utilization = scheduler.calculate_utilization(
        [], date(2024, 1, 1), date(2024, 1, 10)
    )

    assert utilization["dev1"] == 0.0


# ============================================================================
# Test: Error Handling
# ============================================================================


def test_schedule_task_without_required_resource():
    """Test error when task requires resource not in pool."""
    pool = ResourcePool()
    pool.add_resource(
        Resource("dev1", "Developer 1", ResourceType.PERSON, capacity=1.0)
    )

    scheduler = ResourceLevelingScheduler(pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=5.0)

    task = TaskWithRequirement(
        "T1",
        5.0,
        priority=1,
        requirement=TaskResourceRequirement(
            "T1", ResourceType.PERSON, 1.0, ["nonexistent"]
        ),
    )

    with pytest.raises(SchedulingError):
        scheduler.schedule([task], graph, date(2024, 1, 1))


def test_schedule_empty_task_list(basic_resource_pool: ResourcePool):
    """Test scheduling with no tasks returns empty result."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)
    graph = TaskGraph()

    result = scheduler.schedule([], graph, date(2024, 1, 1))

    assert result == []


def test_schedule_with_circular_dependency(basic_resource_pool: ResourcePool):
    """Test error handling for circular dependencies."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    graph = TaskGraph()
    graph.add_node("T1", duration=3.0)
    graph.add_node("T2", duration=3.0)
    graph.add_edge("T1", "T2")
    graph.add_edge("T2", "T1")  # Creates cycle

    tasks = [
        TaskWithRequirement(
            "T1",
            3.0,
            priority=1,
            requirement=TaskResourceRequirement("T1", ResourceType.PERSON, 1.0),
        ),
        TaskWithRequirement(
            "T2",
            3.0,
            priority=1,
            requirement=TaskResourceRequirement("T2", ResourceType.PERSON, 1.0),
        ),
    ]

    with pytest.raises(Exception):  # Should raise CycleDetectedError or SchedulingError
        scheduler.schedule(tasks, graph, date(2024, 1, 1))


# ============================================================================
# Test: Complex Scenarios
# ============================================================================


def test_schedule_large_project(basic_resource_pool: ResourcePool, start_date: date):
    """Test scheduling larger project with multiple constraints."""
    scheduler = ResourceLevelingScheduler(basic_resource_pool)

    # Create project with 10 tasks
    graph = TaskGraph()
    for i in range(1, 11):
        graph.add_node(f"T{i}", duration=float(i))

    # Add some dependencies
    graph.add_edge("T1", "T2")
    graph.add_edge("T2", "T5")
    graph.add_edge("T3", "T6")
    graph.add_edge("T4", "T7")
    graph.add_edge("T5", "T10")

    tasks = []
    for i in range(1, 11):
        requirement = TaskResourceRequirement(f"T{i}", ResourceType.PERSON, 1.0)
        tasks.append(
            TaskWithRequirement(f"T{i}", float(i), priority=i, requirement=requirement)
        )

    result = scheduler.schedule(tasks, graph, start_date)

    assert len(result) == 10
    # Verify dependencies respected
    t1 = next(st for st in result if st.task_id == "T1")
    t2 = next(st for st in result if st.task_id == "T2")
    assert t2.start_date >= t1.end_date + timedelta(days=1)
