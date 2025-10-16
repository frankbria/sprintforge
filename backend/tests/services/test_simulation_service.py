"""
Tests for SimulationService using TDD approach.

This test suite follows TDD methodology:
1. RED: Write tests that fail (service doesn't exist yet)
2. GREEN: Implement minimal code to pass tests
3. REFACTOR: Improve code while maintaining green tests

Coverage target: ≥85%
Pass rate target: 100%
"""

from datetime import date, datetime
from typing import Dict

import pytest

from app.services.scheduler.monte_carlo import TaskDistributionInput
from app.services.simulation_service import (
    SimulationError,
    SimulationResult,
    SimulationService,
)


class TestSimulationServiceBasic:
    """Test basic simulation execution with deterministic tasks."""

    def test_simple_deterministic_simulation(self):
        """Test basic simulation with deterministic (constant) task durations."""
        # Given: Two tasks with constant durations
        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
        ]

        # Deterministic sampler: T001=5 days, T002=3 days
        def deterministic_sampler(task_id: str) -> float:
            return {"T001": 5.0, "T002": 3.0}[task_id]

        # When: Running simulation
        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=deterministic_sampler,
        )

        # Then: Results should be deterministic
        assert isinstance(result, SimulationResult)
        assert result.iterations_run == 100
        assert result.task_count == 2
        # T001(5) + T002(3) = 8 working days
        assert result.mean_duration == pytest.approx(8.0, abs=0.01)
        assert result.median_duration == pytest.approx(8.0, abs=0.01)
        assert result.std_deviation == pytest.approx(0.0, abs=0.01)
        # Check simulation_date is recent
        assert isinstance(result.simulation_date, datetime)
        assert (datetime.now() - result.simulation_date).seconds < 10

    def test_variable_duration_simulation(self):
        """Test simulation with variable task durations."""
        # Given: Single task with variable duration
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        # Variable sampler: Returns 5, 10, 15, ... (cycles)
        iteration_counter = {"count": 0}

        def variable_sampler(task_id: str) -> float:
            iteration_counter["count"] += 1
            # Cycle through 5, 10, 15
            return [5.0, 10.0, 15.0][iteration_counter["count"] % 3]

        # When: Running simulation
        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=300,  # Multiple of 3 for even distribution
            duration_sampler=variable_sampler,
        )

        # Then: Mean should be average of 5, 10, 15
        assert result.mean_duration == pytest.approx(10.0, abs=0.1)
        assert result.std_deviation > 0  # Should have variance
        assert result.median_duration == pytest.approx(10.0, abs=0.5)

    def test_default_iterations_parameter(self):
        """Test that default iterations value is used when not specified."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            duration_sampler=sampler,
            # iterations not specified - should use default
        )

        # Default should be 10000
        assert result.iterations_run == 10000

    def test_custom_percentiles(self):
        """Test simulation with custom percentile values."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
            percentiles=[25, 50, 75],
        )

        # Should have exactly the requested percentiles
        assert set(result.confidence_intervals.keys()) == {25, 50, 75}
        # For deterministic case, all percentiles should be the same
        assert result.confidence_intervals[25] == pytest.approx(5.0, abs=0.01)
        assert result.confidence_intervals[50] == pytest.approx(5.0, abs=0.01)
        assert result.confidence_intervals[75] == pytest.approx(5.0, abs=0.01)

    def test_default_percentiles(self):
        """Test that default percentiles are used when not specified."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
            # percentiles not specified - should use defaults
        )

        # Default percentiles: [10, 50, 90, 95, 99]
        assert set(result.confidence_intervals.keys()) == {10, 50, 90, 95, 99}


class TestSimulationServiceValidation:
    """Test input validation for simulation parameters."""

    def test_empty_task_list_raises_error(self):
        """Test that empty task list raises ValueError."""
        service = SimulationService()

        def sampler(task_id: str) -> float:
            return 5.0

        with pytest.raises(ValueError, match="Task list cannot be empty"):
            service.run_simulation(
                tasks=[],
                project_start=date(2025, 1, 13),
                iterations=100,
                duration_sampler=sampler,
            )

    def test_negative_iterations_raises_error(self):
        """Test that negative iterations raises ValueError."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        with pytest.raises(
            ValueError, match="Iterations must be between 100 and 100000"
        ):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=-100,
                duration_sampler=sampler,
            )

    def test_zero_iterations_raises_error(self):
        """Test that zero iterations raises ValueError."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        with pytest.raises(
            ValueError, match="Iterations must be between 100 and 100000"
        ):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=0,
                duration_sampler=sampler,
            )

    def test_too_few_iterations_raises_error(self):
        """Test that <100 iterations raises ValueError."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        with pytest.raises(
            ValueError, match="Iterations must be between 100 and 100000"
        ):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=50,
                duration_sampler=sampler,
            )

    def test_too_many_iterations_raises_error(self):
        """Test that >100,000 iterations raises ValueError."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        with pytest.raises(
            ValueError, match="Iterations must be between 100 and 100000"
        ):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=150000,
                duration_sampler=sampler,
            )

    def test_invalid_percentile_below_zero(self):
        """Test that percentile < 0 raises ValueError."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        with pytest.raises(ValueError, match="Percentiles must be between 0 and 100"):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=100,
                duration_sampler=sampler,
                percentiles=[-10, 50, 90],
            )

    def test_invalid_percentile_above_100(self):
        """Test that percentile > 100 raises ValueError."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        with pytest.raises(ValueError, match="Percentiles must be between 0 and 100"):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=100,
                duration_sampler=sampler,
                percentiles=[10, 50, 150],
            )

    def test_validate_simulation_input_method(self):
        """Test validate_simulation_input method directly."""
        service = SimulationService()

        # Valid input should not raise
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]
        service.validate_simulation_input(tasks=tasks, iterations=1000)

        # Empty tasks should raise
        with pytest.raises(ValueError, match="Task list cannot be empty"):
            service.validate_simulation_input(tasks=[], iterations=1000)

        # Invalid iterations should raise
        with pytest.raises(ValueError, match="Iterations must be between"):
            service.validate_simulation_input(tasks=tasks, iterations=50)


class TestSimulationServiceErrorHandling:
    """Test error handling for scheduling failures."""

    def test_circular_dependency_raises_simulation_error(self):
        """Test that circular dependencies raise SimulationError."""
        # Create circular dependency: T001 -> T002 -> T001
        tasks = [
            TaskDistributionInput(task_id="T001", dependencies="T002"),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
        ]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        with pytest.raises(SimulationError, match="Circular dependency detected"):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=100,
                duration_sampler=sampler,
            )

    def test_unknown_dependency_raises_simulation_error(self):
        """Test that unknown task dependencies raise SimulationError."""
        tasks = [
            TaskDistributionInput(
                task_id="T001", dependencies="T999"
            ),  # T999 doesn't exist
        ]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        with pytest.raises(SimulationError, match="Unknown dependency"):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=100,
                duration_sampler=sampler,
            )

    def test_negative_sampled_duration_raises_simulation_error(self):
        """Test that negative sampled durations raise SimulationError."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def bad_sampler(task_id: str) -> float:
            return -5.0  # Invalid negative duration

        service = SimulationService()

        with pytest.raises(SimulationError, match="Sampled duration must be positive"):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=100,
                duration_sampler=bad_sampler,
            )

    def test_zero_sampled_duration_raises_simulation_error(self):
        """Test that zero sampled durations raise SimulationError."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def bad_sampler(task_id: str) -> float:
            return 0.0  # Invalid zero duration

        service = SimulationService()

        with pytest.raises(SimulationError, match="Sampled duration must be positive"):
            service.run_simulation(
                tasks=tasks,
                project_start=date(2025, 1, 13),
                iterations=100,
                duration_sampler=bad_sampler,
            )


class TestSimulationServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_task_simulation(self):
        """Test simulation with only one task."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 10.0

        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
        )

        assert result.task_count == 1
        assert result.mean_duration == pytest.approx(10.0, abs=0.01)
        assert result.std_deviation == pytest.approx(0.0, abs=0.01)

    def test_many_tasks_simulation(self):
        """Test simulation with many tasks (20+ tasks)."""
        # Create 25 sequential tasks: T001 -> T002 -> ... -> T025
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]
        for i in range(2, 26):
            prev_task = f"T{i-1:03d}"
            tasks.append(
                TaskDistributionInput(
                    task_id=f"T{i:03d}",
                    dependencies=prev_task,
                )
            )

        def sampler(task_id: str) -> float:
            return 2.0  # Each task is 2 days

        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
        )

        assert result.task_count == 25
        # 25 tasks * 2 days = 50 days
        assert result.mean_duration == pytest.approx(50.0, abs=0.1)

    def test_extreme_percentiles(self):
        """Test simulation with extreme percentile values (0, 100)."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
            percentiles=[0, 50, 100],
        )

        # For deterministic case, all percentiles should be the same
        assert result.confidence_intervals[0] == pytest.approx(5.0, abs=0.01)
        assert result.confidence_intervals[50] == pytest.approx(5.0, abs=0.01)
        assert result.confidence_intervals[100] == pytest.approx(5.0, abs=0.01)

    def test_parallel_tasks_with_shared_dependency(self):
        """Test parallel tasks that share a common dependency."""
        # T001 is completed, then T002 and T003 can run in parallel
        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T001"),
        ]

        def sampler(task_id: str) -> float:
            return {"T001": 5.0, "T002": 3.0, "T003": 4.0}[task_id]

        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
        )

        # T001(5) + max(T002(3), T003(4)) = 5 + 4 = 9 days
        assert result.mean_duration == pytest.approx(9.0, abs=0.1)

    def test_complex_dependency_graph(self):
        """Test simulation with complex multi-level dependencies."""
        # Diamond dependency: T001 -> T002, T003 -> T004
        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T001"),
            TaskDistributionInput(task_id="T004", dependencies="T002,T003"),
        ]

        def sampler(task_id: str) -> float:
            return {"T001": 5.0, "T002": 3.0, "T003": 4.0, "T004": 2.0}[task_id]

        service = SimulationService()
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
        )

        # T001(5) + max(T002(3), T003(4)) + T004(2) = 5 + 4 + 2 = 11 days
        assert result.mean_duration == pytest.approx(11.0, abs=0.1)

    def test_holidays_parameter_integration(self):
        """Test that holidays parameter is passed through to scheduler."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        # This should not raise an error - holidays parameter should be accepted
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
            holidays=[date(2025, 1, 15)],  # One holiday
        )

        # Basic validation that simulation ran
        assert result.iterations_run == 100
        assert result.task_count == 1

    def test_workdays_parameter_integration(self):
        """Test that workdays parameter is passed through to scheduler."""
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        service = SimulationService()

        # This should not raise an error - workdays parameter should be accepted
        result = service.run_simulation(
            tasks=tasks,
            project_start=date(2025, 1, 13),
            iterations=100,
            duration_sampler=sampler,
            workdays={0, 1, 2, 3, 4},  # Mon-Fri
        )

        # Basic validation that simulation ran
        assert result.iterations_run == 100
        assert result.task_count == 1
