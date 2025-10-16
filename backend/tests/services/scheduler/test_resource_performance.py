"""
Performance benchmarks for resource-constrained scheduling.

Tests performance requirements for Phase 2:
- 50 tasks with 10 resources should complete in <5 seconds
"""

import time
from datetime import date

from app.services.scheduler.resource import Resource, ResourcePool, ResourceType
from app.services.scheduler.resource_assignment import TaskResourceRequirement
from app.services.scheduler.resource_cpm import ResourceConstrainedCPM
from app.services.scheduler.resource_leveling import (
    ResourceLevelingScheduler,
    TaskWithRequirement,
)
from app.services.scheduler.task_graph import TaskGraph


def test_resource_leveling_performance_50_tasks_10_resources():
    """Test resource leveling performance: 50 tasks, 10 resources, <5s."""
    # Create resource pool with 10 resources
    pool = ResourcePool()
    for i in range(1, 11):
        pool.add_resource(
            Resource(f"dev{i}", f"Developer {i}", ResourceType.PERSON, capacity=1.0)
        )

    scheduler = ResourceLevelingScheduler(pool)

    # Create task graph with 50 tasks and dependencies
    graph = TaskGraph()
    for i in range(1, 51):
        graph.add_node(f"T{i}", duration=float(i % 10 + 1))

    # Add dependencies to create structure (every 10th task depends on previous)
    for i in range(11, 51):
        if i % 10 == 1:
            graph.add_edge(f"T{i-10}", f"T{i}")

    # Create tasks with resource requirements
    tasks = []
    for i in range(1, 51):
        resource_id = f"dev{i % 10 + 1}"
        requirement = TaskResourceRequirement(
            f"T{i}", ResourceType.PERSON, 1.0, [resource_id]
        )
        task = TaskWithRequirement(
            f"T{i}",
            duration=float(i % 10 + 1),
            priority=i,
            requirement=requirement,
        )
        tasks.append(task)

    # Benchmark scheduling
    start_time = time.time()
    result = scheduler.schedule(tasks, graph, date(2024, 1, 1))
    elapsed = time.time() - start_time

    # Assertions
    assert len(result) == 50
    assert elapsed < 5.0, f"Performance requirement failed: {elapsed:.2f}s (limit: 5s)"
    print(f"✓ Resource leveling: 50 tasks, 10 resources in {elapsed:.2f}s")


def test_resource_cpm_performance_50_tasks_10_resources():
    """Test resource-constrained CPM performance: 50 tasks, 10 resources, <5s."""
    # Create resource pool with 10 resources
    pool = ResourcePool()
    for i in range(1, 11):
        pool.add_resource(
            Resource(f"dev{i}", f"Developer {i}", ResourceType.PERSON, capacity=1.0)
        )

    cpm = ResourceConstrainedCPM(pool)

    # Create task graph with 50 tasks and dependencies
    graph = TaskGraph()
    durations = {}
    requirements = {}

    for i in range(1, 51):
        task_id = f"T{i}"
        duration = float(i % 10 + 1)
        graph.add_node(task_id, duration=duration)
        durations[task_id] = duration

        # Add resource requirement
        resource_id = f"dev{i % 10 + 1}"
        requirements[task_id] = TaskResourceRequirement(
            task_id, ResourceType.PERSON, 1.0, [resource_id]
        )

    # Add dependencies
    for i in range(11, 51):
        if i % 10 == 1:
            graph.add_edge(f"T{i-10}", f"T{i}")

    # Benchmark critical chain calculation
    start_time = time.time()
    result = cpm.calculate_critical_chain(graph, durations, requirements, date(2024, 1, 1))
    elapsed = time.time() - start_time

    # Assertions
    assert len(result.tasks) == 50
    assert elapsed < 5.0, f"Performance requirement failed: {elapsed:.2f}s (limit: 5s)"
    print(f"✓ Resource CPM: 50 tasks, 10 resources in {elapsed:.2f}s")


def test_combined_performance():
    """Test combined performance with realistic scenario."""
    pool = ResourcePool()
    for i in range(1, 11):
        pool.add_resource(
            Resource(f"dev{i}", f"Developer {i}", ResourceType.PERSON, capacity=1.0)
        )

    # Create complex graph
    graph = TaskGraph()
    durations = {}
    requirements = {}

    for i in range(1, 51):
        task_id = f"T{i}"
        duration = float((i * 3) % 10 + 1)
        graph.add_node(task_id, duration=duration)
        durations[task_id] = duration

        resource_id = f"dev{(i * 7) % 10 + 1}"
        requirements[task_id] = TaskResourceRequirement(
            task_id, ResourceType.PERSON, 1.0, [resource_id]
        )

    # Add complex dependencies
    for i in range(2, 51):
        if i % 3 == 0:
            graph.add_edge(f"T{i-1}", f"T{i}")
        if i % 7 == 0 and i > 7:
            graph.add_edge(f"T{i-7}", f"T{i}")

    start_time = time.time()

    # Run both algorithms
    cpm = ResourceConstrainedCPM(pool)
    cpm_result = cpm.calculate_critical_chain(graph, durations, requirements, date(2024, 1, 1))

    scheduler = ResourceLevelingScheduler(pool)
    tasks = [
        TaskWithRequirement(
            task_id,
            durations[task_id],
            priority=int(task_id[1:]),
            requirement=requirements[task_id],
        )
        for task_id in durations.keys()
    ]
    schedule_result = scheduler.schedule(tasks, graph, date(2024, 1, 1))

    elapsed = time.time() - start_time

    assert len(cpm_result.tasks) == 50
    assert len(schedule_result) == 50
    assert elapsed < 10.0, f"Combined performance failed: {elapsed:.2f}s (limit: 10s)"
    print(f"✓ Combined algorithms: 50 tasks in {elapsed:.2f}s")
