"""
Tests for topological sort functionality in TaskGraph.

Tests Kahn's algorithm implementation with various graph structures
and cycle detection.
"""

import pytest
from app.services.scheduler.task_graph import TaskGraph, CycleDetectedError


class TestTopologicalSortBasic:
    """Test basic topological sort functionality."""

    def test_topological_sort_single_node(self):
        """Test topological sort with single node."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        result = graph.topological_sort()
        assert result == ["T001"]

    def test_topological_sort_two_nodes_no_edges(self):
        """Test topological sort with independent nodes."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)

        result = graph.topological_sort()
        assert len(result) == 2
        assert "T001" in result
        assert "T002" in result

    def test_topological_sort_simple_sequence(self):
        """Test topological sort with simple sequence: T001 → T002 → T003."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")

        result = graph.topological_sort()
        assert result == ["T001", "T002", "T003"]

    def test_topological_sort_parallel_tasks(self):
        """Test topological sort with parallel tasks."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        result = graph.topological_sort()

        # T001 must come first
        assert result[0] == "T001"
        # T002 and T003 can be in any order
        assert set(result[1:]) == {"T002", "T003"}

    def test_topological_sort_converging_paths(self):
        """Test topological sort with converging paths."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T003")

        result = graph.topological_sort()

        # T001 and T002 must come before T003
        t003_index = result.index("T003")
        t001_index = result.index("T001")
        t002_index = result.index("T002")

        assert t001_index < t003_index
        assert t002_index < t003_index


class TestTopologicalSortComplexStructures:
    """Test topological sort with complex DAG structures."""

    def test_topological_sort_diamond_structure(self):
        """Test diamond structure: T001 → T002,T003 → T004."""
        graph = TaskGraph()
        for i in range(1, 5):
            graph.add_node(f"T00{i}", duration=float(i))

        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T004")
        graph.add_edge("T003", "T004")

        result = graph.topological_sort()

        # Validate dependencies are respected
        assert result.index("T001") < result.index("T002")
        assert result.index("T001") < result.index("T003")
        assert result.index("T002") < result.index("T004")
        assert result.index("T003") < result.index("T004")

    def test_topological_sort_complex_dag(self):
        """Test complex DAG with multiple paths."""
        graph = TaskGraph()
        for i in range(1, 8):
            graph.add_node(f"T00{i}", duration=float(i))

        # Create complex structure
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T004")
        graph.add_edge("T003", "T004")
        graph.add_edge("T003", "T005")
        graph.add_edge("T004", "T006")
        graph.add_edge("T005", "T006")
        graph.add_edge("T006", "T007")

        result = graph.topological_sort()

        # Validate all dependencies are respected
        assert result.index("T001") < result.index("T002")
        assert result.index("T001") < result.index("T003")
        assert result.index("T002") < result.index("T004")
        assert result.index("T003") < result.index("T004")
        assert result.index("T003") < result.index("T005")
        assert result.index("T004") < result.index("T006")
        assert result.index("T005") < result.index("T006")
        assert result.index("T006") < result.index("T007")

    def test_topological_sort_multiple_roots(self):
        """Test graph with multiple root nodes (no dependencies)."""
        graph = TaskGraph()
        for i in range(1, 6):
            graph.add_node(f"T00{i}", duration=float(i))

        # Two independent roots
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T004")
        graph.add_edge("T003", "T005")
        graph.add_edge("T004", "T005")

        result = graph.topological_sort()

        # T001 and T002 must come before their dependents
        assert result.index("T001") < result.index("T003")
        assert result.index("T002") < result.index("T004")
        assert result.index("T003") < result.index("T005")
        assert result.index("T004") < result.index("T005")

    def test_topological_sort_multiple_leaves(self):
        """Test graph with multiple leaf nodes (no successors)."""
        graph = TaskGraph()
        for i in range(1, 5):
            graph.add_node(f"T00{i}", duration=float(i))

        # Single root, multiple leaves
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")
        graph.add_edge("T001", "T004")

        result = graph.topological_sort()

        # T001 must be first
        assert result[0] == "T001"
        # Other tasks can be in any order
        assert set(result[1:]) == {"T002", "T003", "T004"}

    def test_topological_sort_long_chain(self):
        """Test long sequential chain."""
        graph = TaskGraph()
        n_tasks = 20

        for i in range(1, n_tasks + 1):
            graph.add_node(f"T{i:03d}", duration=float(i))

        for i in range(1, n_tasks):
            graph.add_edge(f"T{i:03d}", f"T{i+1:03d}")

        result = graph.topological_sort()

        # Must be exact sequence
        expected = [f"T{i:03d}" for i in range(1, n_tasks + 1)]
        assert result == expected


class TestCycleDetection:
    """Test cycle detection in topological sort."""

    def test_cycle_detection_simple_cycle(self):
        """Test cycle detection with simple 2-node cycle: T001 → T002 → T001."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T001")

        with pytest.raises(CycleDetectedError, match="Circular dependency"):
            graph.topological_sort()

    def test_cycle_detection_three_node_cycle(self):
        """Test cycle detection with 3-node cycle: T001 → T002 → T003 → T001."""
        graph = TaskGraph()
        for i in range(1, 4):
            graph.add_node(f"T00{i}", duration=float(i))

        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")
        graph.add_edge("T003", "T001")

        with pytest.raises(CycleDetectedError, match="Circular dependency"):
            graph.topological_sort()

    def test_cycle_detection_self_referencing_prevented(self):
        """Test that self-referencing edges are prevented during creation."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        # Self-referencing edge should fail at creation
        with pytest.raises(ValueError, match="self-referencing"):
            graph.add_edge("T001", "T001")

    def test_cycle_detection_complex_cycle(self):
        """Test cycle detection in complex graph with embedded cycle."""
        graph = TaskGraph()
        for i in range(1, 7):
            graph.add_node(f"T00{i}", duration=float(i))

        # Valid part of graph
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")

        # Create cycle: T003 → T004 → T005 → T003
        graph.add_edge("T003", "T004")
        graph.add_edge("T004", "T005")
        graph.add_edge("T005", "T003")

        # More valid edges
        graph.add_edge("T005", "T006")

        with pytest.raises(CycleDetectedError, match="Circular dependency"):
            graph.topological_sort()

    def test_cycle_detection_error_message_includes_tasks(self):
        """Test that cycle error message includes involved tasks."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T001")

        with pytest.raises(CycleDetectedError) as exc_info:
            graph.topological_sort()

        error_msg = str(exc_info.value)
        assert "T001" in error_msg
        assert "T002" in error_msg


class TestTopologicalSortProperties:
    """Test properties and invariants of topological sort."""

    def test_topological_sort_all_tasks_included(self):
        """Test that topological sort includes all tasks."""
        graph = TaskGraph()
        task_ids = [f"T{i:03d}" for i in range(1, 11)]

        for task_id in task_ids:
            graph.add_node(task_id, duration=5.0)

        # Add some edges
        graph.add_edge("T001", "T005")
        graph.add_edge("T002", "T006")
        graph.add_edge("T005", "T009")

        result = graph.topological_sort()

        assert len(result) == len(task_ids)
        assert set(result) == set(task_ids)

    def test_topological_sort_dependency_order_preserved(self):
        """Test that all dependencies come before dependents."""
        graph = TaskGraph()
        for i in range(1, 8):
            graph.add_node(f"T00{i}", duration=float(i))

        edges = [
            ("T001", "T002"),
            ("T001", "T003"),
            ("T002", "T004"),
            ("T003", "T004"),
            ("T004", "T005"),
            ("T005", "T006"),
            ("T006", "T007"),
        ]

        for from_task, to_task in edges:
            graph.add_edge(from_task, to_task)

        result = graph.topological_sort()
        result_index = {task_id: i for i, task_id in enumerate(result)}

        # Verify every edge respects order
        for from_task, to_task in edges:
            assert result_index[from_task] < result_index[to_task], \
                f"{from_task} should come before {to_task}"

    def test_topological_sort_deterministic_with_no_ambiguity(self):
        """Test that sort is deterministic when structure is fully ordered."""
        graph = TaskGraph()
        for i in range(1, 6):
            graph.add_node(f"T00{i}", duration=float(i))

        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")
        graph.add_edge("T003", "T004")
        graph.add_edge("T004", "T005")

        # Run multiple times
        results = [graph.topological_sort() for _ in range(5)]

        # All results should be identical
        for result in results[1:]:
            assert result == results[0]

    def test_topological_sort_empty_graph(self):
        """Test topological sort on empty graph."""
        graph = TaskGraph()
        result = graph.topological_sort()
        assert result == []


class TestTopologicalSortEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_topological_sort_after_adding_nodes_incrementally(self):
        """Test that topological sort works after incremental node addition."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        result1 = graph.topological_sort()
        assert result1 == ["T001"]

        graph.add_node("T002", duration=3.0)
        graph.add_edge("T001", "T002")

        result2 = graph.topological_sort()
        assert result2 == ["T001", "T002"]

        graph.add_node("T003", duration=4.0)
        graph.add_edge("T002", "T003")

        result3 = graph.topological_sort()
        assert result3 == ["T001", "T002", "T003"]

    def test_topological_sort_large_graph(self):
        """Test topological sort on large graph (100 tasks)."""
        graph = TaskGraph()
        n_tasks = 100

        # Create tasks
        for i in range(1, n_tasks + 1):
            graph.add_node(f"T{i:03d}", duration=5.0)

        # Create dependencies: each task depends on previous
        for i in range(1, n_tasks):
            graph.add_edge(f"T{i:03d}", f"T{i+1:03d}")

        result = graph.topological_sort()

        assert len(result) == n_tasks
        assert result == [f"T{i:03d}" for i in range(1, n_tasks + 1)]

    def test_topological_sort_very_wide_graph(self):
        """Test topological sort on very wide graph (many parallel tasks)."""
        graph = TaskGraph()
        graph.add_node("T000", duration=1.0)  # root
        graph.add_node("T999", duration=1.0)  # sink

        # Create 50 parallel tasks
        for i in range(1, 51):
            task_id = f"T{i:03d}"
            graph.add_node(task_id, duration=5.0)
            graph.add_edge("T000", task_id)
            graph.add_edge(task_id, "T999")

        result = graph.topological_sort()

        # T000 must be first, T999 must be last
        assert result[0] == "T000"
        assert result[-1] == "T999"
        assert len(result) == 52
