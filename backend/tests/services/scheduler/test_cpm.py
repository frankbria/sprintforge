"""
Tests for Critical Path Method (CPM) implementation.

Tests forward pass, backward pass, slack calculation, and critical path identification.
"""

import pytest
from app.services.scheduler.task_graph import TaskGraph
from app.services.scheduler.cpm import (
    calculate_forward_pass,
    calculate_backward_pass,
    calculate_critical_path,
)
from app.services.scheduler.models import CriticalPathResult


class TestForwardPass:
    """Test forward pass algorithm (ES, EF calculation)."""

    def test_forward_pass_single_task(self):
        """Test forward pass with single task."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        durations = {"T001": 5.0}

        es_ef = calculate_forward_pass(graph, durations)

        assert es_ef["T001"] == (0.0, 5.0)

    def test_forward_pass_simple_sequence(self):
        """Test forward pass with simple sequence: T001 → T002 → T003."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 4.0}
        es_ef = calculate_forward_pass(graph, durations)

        assert es_ef["T001"] == (0.0, 5.0)
        assert es_ef["T002"] == (5.0, 8.0)
        assert es_ef["T003"] == (8.0, 12.0)

    def test_forward_pass_parallel_paths(self):
        """Test forward pass with parallel paths."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=7.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 7.0}
        es_ef = calculate_forward_pass(graph, durations)

        assert es_ef["T001"] == (0.0, 5.0)
        assert es_ef["T002"] == (5.0, 8.0)
        assert es_ef["T003"] == (5.0, 12.0)

    def test_forward_pass_converging_paths(self):
        """Test forward pass with converging paths."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 4.0}
        es_ef = calculate_forward_pass(graph, durations)

        # T003 must wait for max(EF of T001, EF of T002)
        assert es_ef["T001"] == (0.0, 5.0)
        assert es_ef["T002"] == (0.0, 3.0)
        assert es_ef["T003"] == (5.0, 9.0)  # max(5, 3) + 4

    def test_forward_pass_complex_network(self):
        """Test forward pass with complex dependency network."""
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

        durations = {f"T00{i}": float(i) for i in range(1, 8)}
        es_ef = calculate_forward_pass(graph, durations)

        # Verify key dependencies
        assert es_ef["T001"] == (0.0, 1.0)
        assert es_ef["T002"] == (1.0, 3.0)  # ES=1, EF=1+2
        assert es_ef["T003"] == (1.0, 4.0)  # ES=1, EF=1+3
        assert es_ef["T004"] == (4.0, 8.0)  # ES=max(3,4)=4, EF=4+4
        assert es_ef["T005"] == (4.0, 9.0)  # ES=4 (from T003), EF=4+5
        # T006 has ES=max(EF[T004], EF[T005]) = max(8, 9) = 9
        assert es_ef["T006"] == (9.0, 15.0)  # ES=9, EF=9+6
        assert es_ef["T007"] == (15.0, 22.0)  # ES=15, EF=15+7

    def test_forward_pass_zero_duration_task(self):
        """Test forward pass with zero-duration task (milestone)."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=0.0)  # Milestone
        graph.add_node("T003", duration=3.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")

        durations = {"T001": 5.0, "T002": 0.0, "T003": 3.0}
        es_ef = calculate_forward_pass(graph, durations)

        assert es_ef["T001"] == (0.0, 5.0)
        assert es_ef["T002"] == (5.0, 5.0)  # Zero duration
        assert es_ef["T003"] == (5.0, 8.0)

    def test_forward_pass_fractional_durations(self):
        """Test forward pass with fractional task durations."""
        graph = TaskGraph()
        graph.add_node("T001", duration=2.5)
        graph.add_node("T002", duration=1.75)
        graph.add_edge("T001", "T002")

        durations = {"T001": 2.5, "T002": 1.75}
        es_ef = calculate_forward_pass(graph, durations)

        assert es_ef["T001"] == (0.0, 2.5)
        assert es_ef["T002"] == (2.5, 4.25)


class TestBackwardPass:
    """Test backward pass algorithm (LS, LF calculation)."""

    def test_backward_pass_single_task(self):
        """Test backward pass with single task."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        durations = {"T001": 5.0}
        project_end = 5.0

        ls_lf = calculate_backward_pass(graph, durations, project_end)

        assert ls_lf["T001"] == (0.0, 5.0)

    def test_backward_pass_simple_sequence(self):
        """Test backward pass with simple sequence."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 4.0}
        project_end = 12.0

        ls_lf = calculate_backward_pass(graph, durations, project_end)

        assert ls_lf["T003"] == (8.0, 12.0)
        assert ls_lf["T002"] == (5.0, 8.0)
        assert ls_lf["T001"] == (0.0, 5.0)

    def test_backward_pass_parallel_paths(self):
        """Test backward pass with parallel paths."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=7.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 7.0}
        project_end = 12.0  # max(8, 12) = 12

        ls_lf = calculate_backward_pass(graph, durations, project_end)

        # T002 and T003 are leaf nodes
        assert ls_lf["T002"] == (9.0, 12.0)  # LF=12, LS=12-3
        assert ls_lf["T003"] == (5.0, 12.0)  # LF=12, LS=12-7

        # T001 must finish before earliest LS of successors
        assert ls_lf["T001"] == (0.0, 5.0)  # LF=min(9,5)=5, LS=5-5

    def test_backward_pass_diverging_paths(self):
        """Test backward pass with diverging paths."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_node("T004", duration=2.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T004")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 4.0, "T004": 2.0}
        project_end = 10.0  # T001(5) → T002(3) → T004(2)

        ls_lf = calculate_backward_pass(graph, durations, project_end)

        assert ls_lf["T004"] == (8.0, 10.0)
        assert ls_lf["T002"] == (5.0, 8.0)
        assert ls_lf["T003"] == (6.0, 10.0)  # Has slack
        assert ls_lf["T001"] == (0.0, 5.0)

    def test_backward_pass_complex_network(self):
        """Test backward pass with complex dependency network."""
        graph = TaskGraph()
        for i in range(1, 6):
            graph.add_node(f"T00{i}", duration=float(i))

        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T004")
        graph.add_edge("T003", "T004")
        graph.add_edge("T004", "T005")

        durations = {f"T00{i}": float(i) for i in range(1, 6)}

        # Calculate forward pass first to get project_end
        from app.services.scheduler.cpm import calculate_forward_pass

        es_ef = calculate_forward_pass(graph, durations)
        project_end = es_ef["T005"][1]

        ls_lf = calculate_backward_pass(graph, durations, project_end)

        # Verify T005 (leaf)
        assert ls_lf["T005"] == (project_end - 5.0, project_end)


class TestSlackCalculation:
    """Test slack calculation and critical path identification."""

    def test_slack_calculation_zero_for_critical(self):
        """Test that critical path tasks have zero slack."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_edge("T001", "T002")

        durations = {"T001": 5.0, "T002": 3.0}

        result = calculate_critical_path(graph, durations)

        # All tasks on critical path should have zero slack
        for task_id in result.critical_path:
            assert result.tasks[task_id].slack == 0.0
            assert result.tasks[task_id].is_critical is True

    def test_slack_calculation_positive_for_non_critical(self):
        """Test that non-critical tasks have positive slack."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=7.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 7.0}

        result = calculate_critical_path(graph, durations)

        # T002 has slack (shorter path)
        assert result.tasks["T002"].slack > 0
        assert result.tasks["T002"].is_critical is False

        # T001 and T003 are critical
        assert result.tasks["T001"].slack == 0.0
        assert result.tasks["T003"].slack == 0.0

    def test_critical_path_single_sequence(self):
        """Test critical path identification with single sequence."""
        graph = TaskGraph()
        for i in range(1, 5):
            graph.add_node(f"T00{i}", duration=float(i))

        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")
        graph.add_edge("T003", "T004")

        durations = {f"T00{i}": float(i) for i in range(1, 5)}

        result = calculate_critical_path(graph, durations)

        # All tasks are critical
        assert result.critical_path == ["T001", "T002", "T003", "T004"]
        assert result.project_duration == 10.0  # 1+2+3+4

    def test_critical_path_parallel_paths(self):
        """Test critical path with parallel paths."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)  # Shorter path
        graph.add_node("T003", duration=7.0)  # Longer path (critical)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 7.0}

        result = calculate_critical_path(graph, durations)

        # Critical path goes through longer path
        assert "T001" in result.critical_path
        assert "T003" in result.critical_path
        assert "T002" not in result.critical_path

        assert result.project_duration == 12.0  # 5+7

    def test_critical_path_multiple_critical_paths(self):
        """Test graph with multiple critical paths."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=5.0)  # Same duration
        graph.add_node("T003", duration=5.0)  # Same duration
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        durations = {"T001": 5.0, "T002": 5.0, "T003": 5.0}

        result = calculate_critical_path(graph, durations)

        # Both paths are critical
        assert result.tasks["T001"].is_critical is True
        assert result.tasks["T002"].is_critical is True
        assert result.tasks["T003"].is_critical is True

        assert result.project_duration == 10.0


class TestCPMIntegration:
    """Test complete CPM calculation integration."""

    def test_cpm_complete_calculation(self):
        """Test complete CPM calculation with all fields."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T002", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 4.0}

        result = calculate_critical_path(graph, durations)

        # Verify result structure
        assert isinstance(result, CriticalPathResult)
        assert len(result.tasks) == 3
        assert len(result.critical_path) == 3
        assert result.project_duration == 12.0

        # Verify T001
        t001 = result.tasks["T001"]
        assert t001.es == 0.0
        assert t001.ef == 5.0
        assert t001.ls == 0.0
        assert t001.lf == 5.0
        assert t001.slack == 0.0
        assert t001.is_critical is True

        # Verify T002
        t002 = result.tasks["T002"]
        assert t002.es == 5.0
        assert t002.ef == 8.0
        assert t002.ls == 5.0
        assert t002.lf == 8.0
        assert t002.slack == 0.0
        assert t002.is_critical is True

    def test_cpm_with_dependencies_field(self):
        """Test that dependencies field is populated."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_edge("T001", "T002")

        durations = {"T001": 5.0, "T002": 3.0}

        result = calculate_critical_path(graph, durations)

        assert result.tasks["T001"].dependencies == []
        assert result.tasks["T002"].dependencies == ["T001"]

    def test_cpm_empty_graph(self):
        """Test CPM with empty graph."""
        graph = TaskGraph()
        durations = {}

        result = calculate_critical_path(graph, durations)

        assert len(result.tasks) == 0
        assert result.critical_path == []
        assert result.project_duration == 0.0

    def test_cpm_tolerance_for_floating_point(self):
        """Test that floating point comparison uses tolerance."""
        graph = TaskGraph()
        graph.add_node("T001", duration=1.1)
        graph.add_node("T002", duration=2.2)
        graph.add_edge("T001", "T002")

        durations = {"T001": 1.1, "T002": 2.2}

        result = calculate_critical_path(graph, durations)

        # Should handle floating point precision correctly
        assert result.tasks["T001"].is_critical is True
        assert result.tasks["T002"].is_critical is True
