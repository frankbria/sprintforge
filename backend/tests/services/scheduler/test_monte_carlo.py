"""
Tests for Monte Carlo simulation engine.

Tests cover:
- Basic simulation with known distributions
- Statistical accuracy (mean/median approximation)
- Percentile calculations
- Edge cases (single iteration, deterministic inputs)
- Performance (10,000 iterations should complete in reasonable time)
- Integration with SchedulerService
"""

import time
from datetime import date
from unittest.mock import Mock

import numpy as np
import pytest

from app.services.scheduler.monte_carlo import (
    MonteCarloEngine,
    MonteCarloResult,
    TaskDistributionInput,
)
from app.services.scheduler.scheduler_service import SchedulerService


class TestMonteCarloResult:
    """Test MonteCarloResult model."""

    def test_valid_result_creation(self):
        """Test creating valid MonteCarloResult."""
        result = MonteCarloResult(
            mean_duration=52.3,
            median_duration=51.5,
            std_dev=4.8,
            percentiles={10: 45.2, 50: 51.5, 90: 61.5},
            iterations=10000,
            durations=[50.0, 51.0, 52.0],
        )

        assert result.mean_duration == 52.3
        assert result.median_duration == 51.5
        assert result.std_dev == 4.8
        assert result.percentiles[50] == 51.5
        assert result.iterations == 10000
        assert len(result.durations) == 3

    def test_negative_values_rejected(self):
        """Test that negative durations are rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            MonteCarloResult(
                mean_duration=-1.0,
                median_duration=51.5,
                std_dev=4.8,
                percentiles={50: 51.5},
                iterations=100,
                durations=[50.0],
            )

    def test_zero_iterations_rejected(self):
        """Test that zero iterations is rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            MonteCarloResult(
                mean_duration=52.3,
                median_duration=51.5,
                std_dev=4.8,
                percentiles={50: 51.5},
                iterations=0,
                durations=[50.0],
            )


class TestMonteCarloEngine:
    """Test MonteCarloEngine simulation."""

    def test_engine_creation_default(self):
        """Test creating engine with default parameters."""
        engine = MonteCarloEngine()
        assert engine.iterations == 10000
        assert engine.scheduler is not None

    def test_engine_creation_custom_iterations(self):
        """Test creating engine with custom iteration count."""
        engine = MonteCarloEngine(iterations=5000)
        assert engine.iterations == 5000

    def test_engine_creation_custom_scheduler(self):
        """Test creating engine with custom scheduler."""
        custom_scheduler = SchedulerService()
        engine = MonteCarloEngine(scheduler=custom_scheduler)
        assert engine.scheduler is custom_scheduler

    def test_invalid_iterations_rejected(self):
        """Test that zero or negative iterations are rejected."""
        with pytest.raises(ValueError, match="positive"):
            MonteCarloEngine(iterations=0)

        with pytest.raises(ValueError, match="positive"):
            MonteCarloEngine(iterations=-100)

    def test_empty_task_list_rejected(self):
        """Test that empty task list is rejected."""
        engine = MonteCarloEngine(iterations=100)

        def sampler(task_id: str) -> float:
            return 5.0

        with pytest.raises(ValueError, match="empty"):
            engine.simulate(
                tasks=[],
                duration_sampler=sampler,
                project_start=date(2025, 1, 13),
            )

    def test_single_task_deterministic(self):
        """Test simulation with single task and deterministic duration."""
        engine = MonteCarloEngine(iterations=100)

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
        ]

        # Deterministic sampler always returns 5.0
        def sampler(task_id: str) -> float:
            return 5.0

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
        )

        # With deterministic input, all values should be identical
        assert result.iterations == 100
        assert len(result.durations) == 100
        assert all(d == 5.0 for d in result.durations)
        assert result.mean_duration == 5.0
        assert result.median_duration == 5.0
        assert result.std_dev == 0.0
        assert result.percentiles[50] == 5.0

    def test_single_task_variable_duration(self):
        """Test simulation with single task and variable duration."""
        np.random.seed(42)  # For reproducibility
        engine = MonteCarloEngine(iterations=1000)

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
        ]

        # Sampler returns uniform random between 3 and 7
        def sampler(task_id: str) -> float:
            return np.random.uniform(3.0, 7.0)

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
        )

        # Statistical validation for uniform distribution [3, 7]
        # Expected mean = 5.0, std = (7-3) / sqrt(12) ≈ 1.15
        assert result.iterations == 1000
        assert 4.8 < result.mean_duration < 5.2  # Within reasonable range of 5.0
        assert 4.8 < result.median_duration < 5.2
        assert 1.0 < result.std_dev < 1.4  # Within reasonable range of 1.15
        assert all(3.0 <= d <= 7.0 for d in result.durations)

    def test_multiple_tasks_with_dependencies(self):
        """Test simulation with multiple tasks and dependencies."""
        np.random.seed(42)
        engine = MonteCarloEngine(iterations=1000)

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T001"),
            TaskDistributionInput(task_id="T004", dependencies="T002,T003"),
        ]

        # Sampler: T001=5±1, T002=3±0.5, T003=4±0.5, T004=2±0.5
        duration_ranges = {
            "T001": (4.0, 6.0),
            "T002": (2.5, 3.5),
            "T003": (3.5, 4.5),
            "T004": (1.5, 2.5),
        }

        def sampler(task_id: str) -> float:
            low, high = duration_ranges[task_id]
            return np.random.uniform(low, high)

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
        )

        # Critical path: T001 -> T003 -> T004 or T001 -> T002 -> T004
        # Expected range: (4 + 3.5 + 1.5) to (6 + 4.5 + 2.5) = 9 to 13
        assert result.iterations == 1000
        assert 10.0 < result.mean_duration < 12.0  # Middle of range
        assert all(9.0 <= d <= 13.0 for d in result.durations)

    def test_percentile_calculations(self):
        """Test that percentiles are calculated correctly."""
        np.random.seed(42)
        engine = MonteCarloEngine(iterations=10000)

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
        ]

        # Sampler returns uniform random between 0 and 100
        def sampler(task_id: str) -> float:
            return np.random.uniform(0.0, 100.0)

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            percentiles=[10, 25, 50, 75, 90, 95, 99],
        )

        # For uniform [0, 100], P(x) ≈ x
        assert 8 < result.percentiles[10] < 12
        assert 23 < result.percentiles[25] < 27
        assert 48 < result.percentiles[50] < 52
        assert 73 < result.percentiles[75] < 77
        assert 88 < result.percentiles[90] < 92
        assert 93 < result.percentiles[95] < 97
        assert 98 < result.percentiles[99] < 100

    def test_custom_percentiles(self):
        """Test custom percentile list."""
        engine = MonteCarloEngine(iterations=100)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            percentiles=[5, 50, 95],
        )

        assert 5 in result.percentiles
        assert 50 in result.percentiles
        assert 95 in result.percentiles
        assert len(result.percentiles) == 3

    def test_invalid_percentile_rejected(self):
        """Test that invalid percentiles are rejected."""
        engine = MonteCarloEngine(iterations=100)
        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        with pytest.raises(ValueError, match="between 0 and 100"):
            engine.simulate(
                tasks=tasks,
                duration_sampler=sampler,
                project_start=date(2025, 1, 13),
                percentiles=[150],
            )

    def test_negative_sampled_duration_rejected(self):
        """Test that negative sampled durations cause failure."""
        engine = MonteCarloEngine(iterations=10)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return -1.0  # Invalid

        with pytest.raises(ValueError, match="positive"):
            engine.simulate(
                tasks=tasks,
                duration_sampler=sampler,
                project_start=date(2025, 1, 13),
            )

    def test_zero_sampled_duration_rejected(self):
        """Test that zero sampled durations cause failure."""
        engine = MonteCarloEngine(iterations=10)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 0.0  # Invalid

        with pytest.raises(ValueError, match="positive"):
            engine.simulate(
                tasks=tasks,
                duration_sampler=sampler,
                project_start=date(2025, 1, 13),
            )

    def test_holidays_integration(self):
        """Test that holidays are passed through to scheduler."""
        engine = MonteCarloEngine(iterations=10)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        holidays = [date(2025, 1, 20), date(2025, 1, 21)]

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            holidays=holidays,
        )

        # With 5 working days + 2 holidays in range, duration should still be 5
        # (holidays extend calendar time but not working days)
        assert all(d == 5.0 for d in result.durations)

    def test_workdays_integration(self):
        """Test that custom workdays are passed through to scheduler."""
        engine = MonteCarloEngine(iterations=10)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        # Monday-Thursday only (4-day work week)
        workdays = {0, 1, 2, 3}

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),  # Monday
            workdays=workdays,
        )

        # Duration should still be 5 working days
        assert all(d == 5.0 for d in result.durations)

    def test_scheduler_integration(self):
        """Test that scheduler is called correctly."""
        mock_scheduler = Mock(spec=SchedulerService)
        mock_scheduler.calculate_schedule.return_value = Mock(project_duration=10.0)

        engine = MonteCarloEngine(iterations=5, scheduler=mock_scheduler)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
        )

        # Verify scheduler was called 5 times
        assert mock_scheduler.calculate_schedule.call_count == 5
        assert all(d == 10.0 for d in result.durations)

    def test_performance_10k_iterations(self):
        """Test that 10,000 iterations complete in reasonable time (<5 seconds)."""
        engine = MonteCarloEngine(iterations=10000)

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T002"),
        ]

        def sampler(task_id: str) -> float:
            return np.random.uniform(3.0, 7.0)

        start_time = time.time()

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
        )

        elapsed_time = time.time() - start_time

        assert result.iterations == 10000
        assert elapsed_time < 5.0, f"Performance: {elapsed_time:.2f}s (target: <5s)"

    def test_statistical_accuracy_with_normal_distribution(self):
        """Test statistical accuracy with normal distribution."""
        np.random.seed(42)
        engine = MonteCarloEngine(iterations=50000)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        # Normal distribution: mean=50, std=10
        def sampler(task_id: str) -> float:
            return np.random.normal(50.0, 10.0)

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
        )

        # With 50,000 iterations, should be very close to true values
        assert 49.5 < result.mean_duration < 50.5
        assert 49.5 < result.median_duration < 50.5
        assert 9.8 < result.std_dev < 10.2

        # Normal distribution percentiles (approximately)
        # P10 ≈ mean - 1.28*std ≈ 37.2
        # P90 ≈ mean + 1.28*std ≈ 62.8
        assert 36 < result.percentiles[10] < 38
        assert 62 < result.percentiles[90] < 64

    def test_error_handling_scheduler_failure(self):
        """Test that scheduler failures are properly reported."""
        mock_scheduler = Mock(spec=SchedulerService)
        mock_scheduler.calculate_schedule.side_effect = Exception("Scheduler error")

        engine = MonteCarloEngine(iterations=5, scheduler=mock_scheduler)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        with pytest.raises(ValueError, match="Simulation failed"):
            engine.simulate(
                tasks=tasks,
                duration_sampler=sampler,
                project_start=date(2025, 1, 13),
            )

    def test_single_iteration_edge_case(self):
        """Test edge case with single iteration."""
        engine = MonteCarloEngine(iterations=1)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        def sampler(task_id: str) -> float:
            return 5.0

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
        )

        assert result.iterations == 1
        assert len(result.durations) == 1
        assert result.mean_duration == 5.0
        assert result.std_dev == 0.0

    def test_median_vs_mean_with_skewed_distribution(self):
        """Test that median differs from mean with skewed distribution."""
        np.random.seed(42)
        engine = MonteCarloEngine(iterations=10000)

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        # Right-skewed: most values near 5, occasional high values
        def sampler(task_id: str) -> float:
            if np.random.random() < 0.9:
                return np.random.uniform(4.0, 6.0)
            else:
                return np.random.uniform(15.0, 20.0)  # Outliers

        result = engine.simulate(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
        )

        # Mean should be pulled higher by outliers
        assert result.mean_duration > result.median_duration
        # Median should be closer to the bulk of data (around 5)
        assert 4.5 < result.median_duration < 5.5
