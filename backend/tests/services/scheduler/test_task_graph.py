"""
Tests for TaskGraph data structure.

Following TDD approach: write tests first, then implement.
"""

import pytest
from app.services.scheduler.task_graph import TaskGraph, CycleDetectedError


class TestTaskGraphBasics:
    """Test basic TaskGraph operations."""

    def test_add_node_creates_task(self):
        """Test that add_node creates a node in the graph."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        assert "T001" in graph.nodes
        assert graph.nodes["T001"]["duration"] == 5.0

    def test_add_node_with_metadata(self):
        """Test that add_node stores arbitrary task metadata."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0, name="Design Phase", owner="Alice")

        assert graph.nodes["T001"]["name"] == "Design Phase"
        assert graph.nodes["T001"]["owner"] == "Alice"

    def test_add_node_duplicate_raises_error(self):
        """Test that adding duplicate node raises ValueError."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        with pytest.raises(ValueError, match="already exists"):
            graph.add_node("T001", duration=3.0)

    def test_add_edge_creates_dependency(self):
        """Test that add_edge creates dependency relationship."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_edge("T001", "T002")

        dependencies = graph.get_dependencies("T002")
        assert "T001" in dependencies

    def test_add_edge_validates_from_node_exists(self):
        """Test that add_edge validates from_task exists."""
        graph = TaskGraph()
        graph.add_node("T002", duration=3.0)

        with pytest.raises(ValueError, match="T001.*not found"):
            graph.add_edge("T001", "T002")

    def test_add_edge_validates_to_node_exists(self):
        """Test that add_edge validates to_task exists."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        with pytest.raises(ValueError, match="T002.*not found"):
            graph.add_edge("T001", "T002")

    def test_self_reference_raises_error(self):
        """Test that self-referencing edge raises error."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        with pytest.raises(ValueError, match="self-referencing"):
            graph.add_edge("T001", "T001")

    def test_get_dependencies_returns_list(self):
        """Test that get_dependencies returns list of predecessor task IDs."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T003")

        dependencies = graph.get_dependencies("T003")
        assert len(dependencies) == 2
        assert "T001" in dependencies
        assert "T002" in dependencies

    def test_get_dependencies_empty_for_root_task(self):
        """Test that get_dependencies returns empty list for root tasks."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        dependencies = graph.get_dependencies("T001")
        assert dependencies == []

    def test_get_successors_returns_list(self):
        """Test that get_successors returns list of dependent task IDs."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        successors = graph.get_successors("T001")
        assert len(successors) == 2
        assert "T002" in successors
        assert "T003" in successors

    def test_get_successors_empty_for_leaf_task(self):
        """Test that get_successors returns empty list for leaf tasks."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        successors = graph.get_successors("T001")
        assert successors == []


class TestTaskGraphComplexStructures:
    """Test TaskGraph with complex dependency structures."""

    def test_simple_sequence(self):
        """Test simple sequential dependency: T001 → T002 → T003."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")

        assert graph.get_dependencies("T002") == ["T001"]
        assert graph.get_dependencies("T003") == ["T002"]
        assert graph.get_successors("T001") == ["T002"]
        assert graph.get_successors("T002") == ["T003"]

    def test_parallel_tasks(self):
        """Test parallel tasks: T001 → T002 and T001 → T003."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        assert graph.get_successors("T001") == ["T002", "T003"]
        assert graph.get_dependencies("T002") == ["T001"]
        assert graph.get_dependencies("T003") == ["T001"]

    def test_converging_paths(self):
        """Test converging paths: T001 → T003 and T002 → T003."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T003")

        deps = graph.get_dependencies("T003")
        assert len(deps) == 2
        assert "T001" in deps
        assert "T002" in deps

    def test_diamond_structure(self):
        """Test diamond structure: T001 → T002,T003 → T004."""
        graph = TaskGraph()
        for i in range(1, 5):
            graph.add_node(f"T00{i}", duration=float(i))

        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T004")
        graph.add_edge("T003", "T004")

        # Verify structure
        assert len(graph.get_successors("T001")) == 2
        assert len(graph.get_dependencies("T004")) == 2

    def test_complex_dag(self):
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

        # Verify specific relationships
        assert "T001" in graph.get_dependencies("T002")
        assert "T006" in graph.get_successors("T004")
        assert len(graph.get_dependencies("T006")) == 2


class TestTaskGraphValidation:
    """Test TaskGraph validation and error handling."""

    def test_get_dependencies_validates_task_exists(self):
        """Test that get_dependencies validates task exists."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        with pytest.raises(ValueError, match="T999.*not found"):
            graph.get_dependencies("T999")

    def test_get_successors_validates_task_exists(self):
        """Test that get_successors validates task exists."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)

        with pytest.raises(ValueError, match="T999.*not found"):
            graph.get_successors("T999")

    def test_duplicate_edge_ignored(self):
        """Test that adding duplicate edge is idempotent."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)

        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T002")  # Should not raise error

        dependencies = graph.get_dependencies("T002")
        assert dependencies == ["T001"]


class TestTaskGraphProperties:
    """Test TaskGraph properties and utility methods."""

    def test_node_count(self):
        """Test that graph tracks node count correctly."""
        graph = TaskGraph()
        assert len(graph.nodes) == 0

        graph.add_node("T001", duration=5.0)
        assert len(graph.nodes) == 1

        graph.add_node("T002", duration=3.0)
        assert len(graph.nodes) == 2

    def test_has_dependencies(self):
        """Test checking if task has dependencies."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_edge("T001", "T002")

        assert not graph.has_dependencies("T001")
        assert graph.has_dependencies("T002")

    def test_is_empty(self):
        """Test checking if graph is empty."""
        graph = TaskGraph()
        assert graph.is_empty()

        graph.add_node("T001", duration=5.0)
        assert not graph.is_empty()
