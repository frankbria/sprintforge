"""
Test suite for CCPM buffer management.

Tests buffer calculation, placement, consumption tracking, and status monitoring
following Critical Chain Project Management methodology.
"""

import pytest

from app.services.scheduler.ccpm_buffers import (
    Buffer,
    BufferStatus,
    BufferType,
    CCPMBufferCalculator,
)
from app.services.scheduler.task_graph import TaskGraph


class TestBuffer:
    """Test Buffer data class."""

    def test_buffer_creation_project(self):
        """Test creating a project buffer."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=0.0,
        )
        assert buffer.buffer_type == BufferType.PROJECT
        assert buffer.size == 10.0
        assert buffer.location == "end"
        assert buffer.consumption == 0.0

    def test_buffer_creation_feeding(self):
        """Test creating a feeding buffer."""
        buffer = Buffer(
            buffer_type=BufferType.FEEDING,
            size=5.0,
            location="T003",
            consumption=2.0,
        )
        assert buffer.buffer_type == BufferType.FEEDING
        assert buffer.size == 5.0
        assert buffer.location == "T003"
        assert buffer.consumption == 2.0

    def test_buffer_consumption_percentage(self):
        """Test buffer consumption percentage calculation."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=3.0,
        )
        assert buffer.consumption_percentage() == 30.0

    def test_buffer_consumption_percentage_zero_size(self):
        """Test consumption percentage with zero-sized buffer."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=0.0,
            location="end",
            consumption=0.0,
        )
        assert buffer.consumption_percentage() == 0.0

    def test_buffer_consumption_percentage_full(self):
        """Test consumption percentage when buffer is fully consumed."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=10.0,
        )
        assert buffer.consumption_percentage() == 100.0

    def test_buffer_consumption_percentage_over(self):
        """Test consumption percentage when buffer is over-consumed."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=12.0,
        )
        assert buffer.consumption_percentage() == 120.0

    def test_buffer_status_green(self):
        """Test buffer status when consumption is in green zone (<33%)."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=2.0,
        )
        assert buffer.status() == BufferStatus.GREEN

    def test_buffer_status_yellow(self):
        """Test buffer status when consumption is in yellow zone (33-66%)."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=5.0,
        )
        assert buffer.status() == BufferStatus.YELLOW

    def test_buffer_status_red(self):
        """Test buffer status when consumption is in red zone (>66%)."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=7.0,
        )
        assert buffer.status() == BufferStatus.RED

    def test_buffer_status_boundary_green_yellow(self):
        """Test buffer status at green/yellow boundary (~33%)."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=3.3,
        )
        # 3.3/10 = 32.999...% due to floating point, should be GREEN (<=33%)
        assert buffer.status() == BufferStatus.GREEN

    def test_buffer_status_boundary_yellow_red(self):
        """Test buffer status at yellow/red boundary (~66%)."""
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=6.6,
        )
        # 6.6/10 = 65.999...% due to floating point, should be YELLOW (<=66%)
        assert buffer.status() == BufferStatus.YELLOW


class TestCCPMBufferCalculator:
    """Test CCPM buffer calculation and tracking."""

    def test_project_buffer_simple_method(self):
        """Test project buffer calculation using simple 50% method."""
        calculator = CCPMBufferCalculator(method="simple")

        # Critical chain with total duration 20 days
        critical_chain = ["T001", "T002", "T003"]
        durations = {"T001": 5.0, "T002": 8.0, "T003": 7.0}

        buffer_size = calculator.calculate_project_buffer(critical_chain, durations)

        # 50% of (5 + 8 + 7) = 10.0
        assert buffer_size == 10.0

    def test_project_buffer_root_square_method(self):
        """Test project buffer calculation using Root Square Method."""
        calculator = CCPMBufferCalculator(method="root_square")

        # Critical chain
        critical_chain = ["T001", "T002", "T003"]
        durations = {"T001": 3.0, "T002": 4.0, "T003": 5.0}

        buffer_size = calculator.calculate_project_buffer(critical_chain, durations)

        # √(3² + 4² + 5²) = √(9 + 16 + 25) = √50 ≈ 7.071
        assert abs(buffer_size - 7.071) < 0.01

    def test_project_buffer_empty_chain(self):
        """Test project buffer with empty critical chain."""
        calculator = CCPMBufferCalculator()

        buffer_size = calculator.calculate_project_buffer([], {})

        assert buffer_size == 0.0

    def test_project_buffer_single_task(self):
        """Test project buffer with single task chain."""
        calculator = CCPMBufferCalculator(method="simple")

        critical_chain = ["T001"]
        durations = {"T001": 10.0}

        buffer_size = calculator.calculate_project_buffer(critical_chain, durations)

        assert buffer_size == 5.0  # 50% of 10

    def test_feeding_buffer_calculation(self):
        """Test feeding buffer calculation (50% of chain duration)."""
        calculator = CCPMBufferCalculator()

        feeding_chain = ["T004", "T005"]
        durations = {"T004": 6.0, "T005": 4.0}

        buffer_size = calculator.calculate_feeding_buffer(feeding_chain, durations)

        # 50% of (6 + 4) = 5.0
        assert buffer_size == 5.0

    def test_feeding_buffer_single_task(self):
        """Test feeding buffer with single task."""
        calculator = CCPMBufferCalculator()

        feeding_chain = ["T004"]
        durations = {"T004": 8.0}

        buffer_size = calculator.calculate_feeding_buffer(feeding_chain, durations)

        assert buffer_size == 4.0  # 50% of 8

    def test_feeding_buffer_empty_chain(self):
        """Test feeding buffer with empty chain."""
        calculator = CCPMBufferCalculator()

        buffer_size = calculator.calculate_feeding_buffer([], {})

        assert buffer_size == 0.0

    def test_identify_feeding_chains_simple(self):
        """Test identifying feeding chains in simple graph."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_node("T004", duration=6.0)

        # T001 → T003 → T004 (critical chain)
        # T002 → T003 (feeding chain)
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T003")
        graph.add_edge("T003", "T004")

        calculator = CCPMBufferCalculator()
        critical_chain = ["T001", "T003", "T004"]

        feeding_chains = calculator.identify_feeding_chains(graph, critical_chain)

        # Should find feeding chain T002 joining at T003
        assert len(feeding_chains) == 1
        assert feeding_chains[0]["chain"] == ["T002"]
        assert feeding_chains[0]["join_point"] == "T003"

    def test_identify_feeding_chains_multiple(self):
        """Test identifying multiple feeding chains."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=4.0)
        graph.add_node("T004", duration=2.0)
        graph.add_node("T005", duration=6.0)

        # T001 → T003 → T005 (critical chain)
        # T002 → T003 (feeding chain 1)
        # T004 → T005 (feeding chain 2)
        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T003")
        graph.add_edge("T003", "T005")
        graph.add_edge("T004", "T005")

        calculator = CCPMBufferCalculator()
        critical_chain = ["T001", "T003", "T005"]

        feeding_chains = calculator.identify_feeding_chains(graph, critical_chain)

        assert len(feeding_chains) == 2
        # Should find both feeding chains
        chain_tasks = [fc["chain"] for fc in feeding_chains]
        assert ["T002"] in chain_tasks
        assert ["T004"] in chain_tasks

    def test_identify_feeding_chains_no_feeding(self):
        """Test identifying feeding chains when none exist."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)

        # Simple chain with no feeding paths
        graph.add_edge("T001", "T002")

        calculator = CCPMBufferCalculator()
        critical_chain = ["T001", "T002"]

        feeding_chains = calculator.identify_feeding_chains(graph, critical_chain)

        assert len(feeding_chains) == 0

    def test_identify_feeding_chains_nested(self):
        """Test identifying nested feeding chains."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=2.0)
        graph.add_node("T004", duration=4.0)

        # T001 → T004 (critical chain)
        # T002 → T003 → T004 (feeding chain)
        graph.add_edge("T001", "T004")
        graph.add_edge("T002", "T003")
        graph.add_edge("T003", "T004")

        calculator = CCPMBufferCalculator()
        critical_chain = ["T001", "T004"]

        feeding_chains = calculator.identify_feeding_chains(graph, critical_chain)

        assert len(feeding_chains) == 1
        assert feeding_chains[0]["chain"] == ["T002", "T003"]
        assert feeding_chains[0]["join_point"] == "T004"

    def test_calculate_all_buffers_simple(self):
        """Test calculating all buffers for simple project."""
        graph = TaskGraph()
        graph.add_node("T001", duration=10.0)
        graph.add_node("T002", duration=5.0)
        graph.add_node("T003", duration=8.0)

        graph.add_edge("T001", "T003")
        graph.add_edge("T002", "T003")

        calculator = CCPMBufferCalculator(method="simple")
        critical_chain = ["T001", "T003"]
        durations = {"T001": 10.0, "T002": 5.0, "T003": 8.0}

        buffers = calculator.calculate_all_buffers(graph, critical_chain, durations)

        # Should have project buffer and one feeding buffer
        assert len(buffers) == 2

        # Find project buffer
        project_buffers = [b for b in buffers if b.buffer_type == BufferType.PROJECT]
        assert len(project_buffers) == 1
        assert project_buffers[0].size == 9.0  # 50% of (10 + 8)
        assert project_buffers[0].location == "end"

        # Find feeding buffer
        feeding_buffers = [b for b in buffers if b.buffer_type == BufferType.FEEDING]
        assert len(feeding_buffers) == 1
        assert feeding_buffers[0].size == 2.5  # 50% of 5
        assert feeding_buffers[0].location == "T003"

    def test_calculate_all_buffers_no_feeding(self):
        """Test calculating buffers when no feeding chains exist."""
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=7.0)

        graph.add_edge("T001", "T002")

        calculator = CCPMBufferCalculator(method="simple")
        critical_chain = ["T001", "T002"]
        durations = {"T001": 5.0, "T002": 7.0}

        buffers = calculator.calculate_all_buffers(graph, critical_chain, durations)

        # Should only have project buffer
        assert len(buffers) == 1
        assert buffers[0].buffer_type == BufferType.PROJECT
        assert buffers[0].size == 6.0  # 50% of (5 + 7)

    def test_track_buffer_consumption_project(self):
        """Test tracking project buffer consumption."""
        calculator = CCPMBufferCalculator()

        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=0.0,
        )

        # Consume 3 days of buffer
        calculator.track_buffer_consumption(buffer, 3.0)

        assert buffer.consumption == 3.0
        assert buffer.status() == BufferStatus.GREEN

    def test_track_buffer_consumption_multiple(self):
        """Test tracking multiple consumption events."""
        calculator = CCPMBufferCalculator()

        buffer = Buffer(
            buffer_type=BufferType.FEEDING,
            size=10.0,
            location="T003",
            consumption=0.0,
        )

        # Multiple consumption events
        calculator.track_buffer_consumption(buffer, 2.0)
        calculator.track_buffer_consumption(buffer, 3.0)
        calculator.track_buffer_consumption(buffer, 2.0)

        assert buffer.consumption == 7.0
        assert buffer.status() == BufferStatus.RED

    def test_track_buffer_consumption_zero(self):
        """Test tracking zero consumption."""
        calculator = CCPMBufferCalculator()

        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=0.0,
        )

        calculator.track_buffer_consumption(buffer, 0.0)

        assert buffer.consumption == 0.0
        assert buffer.status() == BufferStatus.GREEN

    def test_get_buffer_status_summary(self):
        """Test getting summary of all buffer statuses."""
        calculator = CCPMBufferCalculator()

        buffers = [
            Buffer(
                buffer_type=BufferType.PROJECT,
                size=10.0,
                location="end",
                consumption=2.0,
            ),  # Green
            Buffer(
                buffer_type=BufferType.FEEDING,
                size=10.0,
                location="T003",
                consumption=5.0,
            ),  # Yellow
            Buffer(
                buffer_type=BufferType.FEEDING,
                size=10.0,
                location="T005",
                consumption=8.0,
            ),  # Red
        ]

        summary = calculator.get_buffer_status_summary(buffers)

        assert summary["total_buffers"] == 3
        assert summary["green_count"] == 1
        assert summary["yellow_count"] == 1
        assert summary["red_count"] == 1
        assert summary["critical_buffers"] == 1  # Red buffers

    def test_get_buffer_status_summary_all_green(self):
        """Test buffer status summary when all buffers are green."""
        calculator = CCPMBufferCalculator()

        buffers = [
            Buffer(
                buffer_type=BufferType.PROJECT,
                size=10.0,
                location="end",
                consumption=1.0,
            ),
            Buffer(
                buffer_type=BufferType.FEEDING,
                size=10.0,
                location="T003",
                consumption=2.0,
            ),
        ]

        summary = calculator.get_buffer_status_summary(buffers)

        assert summary["total_buffers"] == 2
        assert summary["green_count"] == 2
        assert summary["yellow_count"] == 0
        assert summary["red_count"] == 0
        assert summary["critical_buffers"] == 0

    def test_method_validation_invalid(self):
        """Test that invalid calculation method raises error."""
        with pytest.raises(ValueError, match="Invalid buffer calculation method"):
            CCPMBufferCalculator(method="invalid_method")

    def test_method_validation_valid_simple(self):
        """Test that 'simple' method is valid."""
        calculator = CCPMBufferCalculator(method="simple")
        assert calculator.method == "simple"

    def test_method_validation_valid_root_square(self):
        """Test that 'root_square' method is valid."""
        calculator = CCPMBufferCalculator(method="root_square")
        assert calculator.method == "root_square"


class TestBufferIntegration:
    """Integration tests for buffer management with real project scenarios."""

    def test_complex_project_all_buffers(self):
        """Test buffer calculation for complex project with multiple feeding chains."""
        # Create realistic project graph
        graph = TaskGraph()
        for i in range(1, 8):
            graph.add_node(f"T{i:03d}", duration=float(i + 2))

        # Critical chain: T001 → T003 → T005 → T007
        graph.add_edge("T001", "T003")
        graph.add_edge("T003", "T005")
        graph.add_edge("T005", "T007")

        # Feeding chains
        graph.add_edge("T002", "T003")  # Feeding to T003
        graph.add_edge("T004", "T005")  # Feeding to T005
        graph.add_edge("T006", "T007")  # Feeding to T007

        calculator = CCPMBufferCalculator(method="simple")
        critical_chain = ["T001", "T003", "T005", "T007"]
        durations = {f"T{i:03d}": float(i + 2) for i in range(1, 8)}

        buffers = calculator.calculate_all_buffers(graph, critical_chain, durations)

        # Should have 1 project buffer + 3 feeding buffers
        assert len(buffers) == 4

        project_buffers = [b for b in buffers if b.buffer_type == BufferType.PROJECT]
        feeding_buffers = [b for b in buffers if b.buffer_type == BufferType.FEEDING]

        assert len(project_buffers) == 1
        assert len(feeding_buffers) == 3

        # Verify all feeding buffers have correct join points
        join_points = [fb.location for fb in feeding_buffers]
        assert "T003" in join_points
        assert "T005" in join_points
        assert "T007" in join_points

    def test_buffer_lifecycle_consumption_tracking(self):
        """Test complete buffer lifecycle with consumption tracking."""
        calculator = CCPMBufferCalculator()

        # Create initial buffer
        buffer = Buffer(
            buffer_type=BufferType.PROJECT,
            size=10.0,
            location="end",
            consumption=0.0,
        )

        # Track consumption over time
        assert buffer.status() == BufferStatus.GREEN

        # Day 1-5: Small delays (stays green)
        calculator.track_buffer_consumption(buffer, 2.0)
        assert buffer.status() == BufferStatus.GREEN

        # Day 6-10: More delays (moves to yellow)
        calculator.track_buffer_consumption(buffer, 2.5)
        assert buffer.status() == BufferStatus.YELLOW

        # Day 11-15: Critical delays (moves to red)
        calculator.track_buffer_consumption(buffer, 3.0)
        assert buffer.status() == BufferStatus.RED
        assert buffer.consumption == 7.5
        assert buffer.consumption_percentage() == 75.0
