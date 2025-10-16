"""
Tests for Risk Analyzer - Monte Carlo risk integration.

Tests cover:
- TaskCriticalityData and RiskMetrics models
- Critical path tracking across iterations
- Criticality index calculation
- Risk driver identification
- Completion confidence calculation
- Full integration with MonteCarloEngine
"""

from datetime import date

import pytest

from app.services.scheduler.monte_carlo import MonteCarloEngine, TaskDistributionInput
from app.services.scheduler.risk_analyzer import (
    RiskAnalyzer,
    RiskMetrics,
    TaskCriticalityData,
)
from app.services.scheduler.scheduler_service import SchedulerService


class TestTaskCriticalityData:
    """Test TaskCriticalityData model."""

    def test_basic_instantiation(self):
        """Test creating TaskCriticalityData with valid values."""
        data = TaskCriticalityData(
            task_id="T001",
            criticality_index=0.85,
            times_critical=850,
            total_iterations=1000,
            mean_duration=5.2,
            duration_variance=1.3,
            is_risk_driver=True,
        )

        assert data.task_id == "T001"
        assert data.criticality_index == 0.85
        assert data.times_critical == 850
        assert data.total_iterations == 1000
        assert data.mean_duration == 5.2
        assert data.duration_variance == 1.3
        assert data.is_risk_driver is True

    def test_criticality_index_validation(self):
        """Test criticality_index must be between 0 and 1."""
        # Valid values
        TaskCriticalityData(
            task_id="T001",
            criticality_index=0.0,
            times_critical=0,
            total_iterations=1000,
            mean_duration=5.0,
            duration_variance=1.0,
            is_risk_driver=False,
        )

        TaskCriticalityData(
            task_id="T001",
            criticality_index=1.0,
            times_critical=1000,
            total_iterations=1000,
            mean_duration=5.0,
            duration_variance=1.0,
            is_risk_driver=False,
        )

        # Invalid values should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            TaskCriticalityData(
                task_id="T001",
                criticality_index=1.5,
                times_critical=1500,
                total_iterations=1000,
                mean_duration=5.0,
                duration_variance=1.0,
                is_risk_driver=False,
            )

        with pytest.raises(Exception):
            TaskCriticalityData(
                task_id="T001",
                criticality_index=-0.1,
                times_critical=-10,
                total_iterations=1000,
                mean_duration=5.0,
                duration_variance=1.0,
                is_risk_driver=False,
            )

    def test_dict_conversion(self):
        """Test converting to dictionary."""
        data = TaskCriticalityData(
            task_id="T001",
            criticality_index=0.75,
            times_critical=750,
            total_iterations=1000,
            mean_duration=5.0,
            duration_variance=1.5,
            is_risk_driver=True,
        )

        d = data.dict()
        assert d["task_id"] == "T001"
        assert d["criticality_index"] == 0.75
        assert d["is_risk_driver"] is True


class TestRiskMetrics:
    """Test RiskMetrics model."""

    def test_basic_instantiation(self):
        """Test creating RiskMetrics with valid data."""
        task_data = TaskCriticalityData(
            task_id="T001",
            criticality_index=0.9,
            times_critical=900,
            total_iterations=1000,
            mean_duration=5.0,
            duration_variance=1.0,
            is_risk_driver=True,
        )

        metrics = RiskMetrics(
            probabilistic_critical_path=["T001", "T002", "T003"],
            task_criticality={"T001": task_data},
            risk_drivers=["T001"],
            confidence_intervals={
                50: date(2025, 2, 15),
                75: date(2025, 2, 20),
                90: date(2025, 2, 28),
            },
        )

        assert len(metrics.probabilistic_critical_path) == 3
        assert "T001" in metrics.task_criticality
        assert len(metrics.risk_drivers) == 1
        assert 50 in metrics.confidence_intervals

    def test_empty_risk_metrics(self):
        """Test RiskMetrics with empty values."""
        metrics = RiskMetrics(
            probabilistic_critical_path=[],
            task_criticality={},
            risk_drivers=[],
            confidence_intervals={},
        )

        assert len(metrics.probabilistic_critical_path) == 0
        assert len(metrics.task_criticality) == 0
        assert len(metrics.risk_drivers) == 0
        assert len(metrics.confidence_intervals) == 0


class TestRiskAnalyzerBasic:
    """Test basic RiskAnalyzer functionality."""

    def test_initialization(self):
        """Test RiskAnalyzer initialization."""
        monte_carlo = MonteCarloEngine(iterations=100)
        scheduler = SchedulerService()

        analyzer = RiskAnalyzer(
            monte_carlo_engine=monte_carlo,
            scheduler=scheduler,
        )

        assert analyzer.monte_carlo_engine is not None
        assert analyzer.scheduler is not None

    def test_initialization_with_defaults(self):
        """Test RiskAnalyzer creates default dependencies if not provided."""
        analyzer = RiskAnalyzer()

        assert analyzer.monte_carlo_engine is not None
        assert analyzer.scheduler is not None


class TestCriticalPathTracking:
    """Test critical path tracking across Monte Carlo iterations."""

    def test_track_critical_paths_simple(self):
        """Test tracking critical paths in simple linear project."""
        analyzer = RiskAnalyzer()

        # Simple sampler: always return fixed durations
        def sampler(task_id: str) -> float:
            return {"T001": 5.0, "T002": 3.0, "T003": 2.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T002"),
        ]

        # With fixed durations, all tasks should always be critical
        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=10,
        )

        # All tasks on linear path should have 100% criticality
        assert metrics.task_criticality["T001"].criticality_index == 1.0
        assert metrics.task_criticality["T002"].criticality_index == 1.0
        assert metrics.task_criticality["T003"].criticality_index == 1.0

    def test_track_critical_paths_parallel(self):
        """Test tracking critical paths with parallel branches."""
        analyzer = RiskAnalyzer()

        # Deterministic durations with one clearly longer path
        def sampler(task_id: str) -> float:
            return {
                "T001": 5.0,  # Start
                "T002": 10.0,  # Long path
                "T003": 2.0,  # Short path
                "T004": 3.0,  # End (depends on both T002 and T003)
            }[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T001"),
            TaskDistributionInput(task_id="T004", dependencies="T002,T003"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=10,
        )

        # T001, T002, T004 should always be critical (longer path)
        assert metrics.task_criticality["T001"].criticality_index == 1.0
        assert metrics.task_criticality["T002"].criticality_index == 1.0
        assert metrics.task_criticality["T004"].criticality_index == 1.0

        # T003 should never be critical (shorter path)
        assert metrics.task_criticality["T003"].criticality_index == 0.0

    def test_criticality_index_with_variance(self):
        """Test criticality index calculation with varying durations."""
        analyzer = RiskAnalyzer()

        # Simulate variance in parallel paths
        iteration_count = [0]

        def sampler(task_id: str) -> float:
            iteration_count[0] += 1
            iter_num = (iteration_count[0] - 1) // 4  # 4 tasks per iteration

            # Alternate which path is critical
            if iter_num % 2 == 0:
                # Even iterations: T002 longer
                return {
                    "T001": 5.0,
                    "T002": 10.0,  # Critical
                    "T003": 3.0,
                    "T004": 2.0,
                }[task_id]
            else:
                # Odd iterations: T003 longer
                return {
                    "T001": 5.0,
                    "T002": 3.0,
                    "T003": 10.0,  # Critical
                    "T004": 2.0,
                }[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T001"),
            TaskDistributionInput(task_id="T004", dependencies="T002,T003"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=10,  # 5 even, 5 odd
        )

        # T001 and T004 always critical
        assert metrics.task_criticality["T001"].criticality_index == 1.0
        assert metrics.task_criticality["T004"].criticality_index == 1.0

        # T002 and T003 should each be critical ~50% of time
        assert 0.4 <= metrics.task_criticality["T002"].criticality_index <= 0.6
        assert 0.4 <= metrics.task_criticality["T003"].criticality_index <= 0.6

    def test_probabilistic_critical_path_ordering(self):
        """Test probabilistic critical path is ordered by criticality."""
        analyzer = RiskAnalyzer()

        iteration_count = [0]

        def sampler(task_id: str) -> float:
            iteration_count[0] += 1
            iter_num = (iteration_count[0] - 1) // 4

            if iter_num % 2 == 0:
                return {"T001": 5.0, "T002": 10.0, "T003": 3.0, "T004": 2.0}[task_id]
            else:
                return {"T001": 5.0, "T002": 3.0, "T003": 10.0, "T004": 2.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T001"),
            TaskDistributionInput(task_id="T004", dependencies="T002,T003"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=10,
        )

        # Probabilistic critical path should list highest criticality tasks first
        path = metrics.probabilistic_critical_path
        assert "T001" in path  # Always critical
        assert "T004" in path  # Always critical

        # Should be ordered by criticality index (descending)
        criticalities = [
            metrics.task_criticality[tid].criticality_index for tid in path
        ]
        assert criticalities == sorted(criticalities, reverse=True)


class TestRiskDriverIdentification:
    """Test risk driver identification."""

    def test_high_criticality_high_variance_is_risk_driver(self):
        """Test tasks with high criticality and high variance are risk drivers."""
        analyzer = RiskAnalyzer()

        # Create variance in one task's duration
        import random

        random.seed(42)

        def sampler(task_id: str) -> float:
            if task_id == "T002":
                # High variance: 5-15 days
                return random.uniform(5.0, 15.0)
            return {"T001": 5.0, "T003": 3.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),  # High variance
            TaskDistributionInput(task_id="T003", dependencies="T002"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=100,
        )

        # T002 has high criticality (always on path) and high variance
        assert metrics.task_criticality["T002"].is_risk_driver is True
        assert "T002" in metrics.risk_drivers

    def test_low_criticality_high_variance_not_risk_driver(self):
        """Test tasks with low criticality but high variance are NOT risk drivers."""
        analyzer = RiskAnalyzer()

        import random

        random.seed(42)

        def sampler(task_id: str) -> float:
            if task_id == "T003":
                # High variance but not critical
                return random.uniform(1.0, 5.0)
            return {
                "T001": 5.0,
                "T002": 10.0,  # Always longer than T003
                "T004": 2.0,
            }[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(
                task_id="T003", dependencies="T001"
            ),  # High variance, low criticality
            TaskDistributionInput(task_id="T004", dependencies="T002,T003"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=100,
        )

        # T003 has high variance but low criticality
        assert metrics.task_criticality["T003"].is_risk_driver is False
        assert "T003" not in metrics.risk_drivers

    def test_high_criticality_low_variance_not_risk_driver(self):
        """Test tasks with high criticality but low variance are NOT risk drivers."""
        analyzer = RiskAnalyzer()

        def sampler(task_id: str) -> float:
            # All tasks have fixed (low variance) durations
            return {"T001": 5.0, "T002": 3.0, "T003": 2.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T002"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=50,
        )

        # All tasks have 100% criticality but zero variance
        # None should be risk drivers
        for task_id in ["T001", "T002", "T003"]:
            assert metrics.task_criticality[task_id].criticality_index == 1.0
            assert metrics.task_criticality[task_id].duration_variance == 0.0
            assert metrics.task_criticality[task_id].is_risk_driver is False

        assert len(metrics.risk_drivers) == 0


class TestCompletionConfidence:
    """Test completion confidence calculation."""

    def test_confidence_intervals_basic(self):
        """Test confidence interval calculation."""
        analyzer = RiskAnalyzer()

        def sampler(task_id: str) -> float:
            return {"T001": 5.0, "T002": 3.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=50,
        )

        # Should have standard confidence intervals
        assert 50 in metrics.confidence_intervals
        assert 75 in metrics.confidence_intervals
        assert 90 in metrics.confidence_intervals

        # Dates should be reasonable
        for percentile, completion_date in metrics.confidence_intervals.items():
            assert completion_date >= date(2025, 1, 13)

    def test_confidence_intervals_ordered(self):
        """Test confidence intervals are properly ordered."""
        analyzer = RiskAnalyzer()

        def sampler(task_id: str) -> float:
            return {"T001": 5.0, "T002": 3.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=50,
        )

        # Higher confidence should have later dates
        assert metrics.confidence_intervals[50] <= metrics.confidence_intervals[75]
        assert metrics.confidence_intervals[75] <= metrics.confidence_intervals[90]

    def test_confidence_with_variance(self):
        """Test confidence intervals reflect task duration variance."""
        analyzer = RiskAnalyzer()

        import random

        random.seed(42)

        def sampler(task_id: str) -> float:
            if task_id == "T002":
                # High variance
                return random.uniform(1.0, 10.0)
            return {"T001": 5.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=100,
        )

        # With high variance, P90 should be significantly later than P50
        days_diff = (
            metrics.confidence_intervals[90] - metrics.confidence_intervals[50]
        ).days

        assert days_diff > 3  # Should have noticeable spread


class TestRiskAnalyzerIntegration:
    """Test full risk analysis integration."""

    def test_complete_risk_analysis(self):
        """Test complete risk analysis workflow."""
        analyzer = RiskAnalyzer()

        import random

        random.seed(42)

        def sampler(task_id: str) -> float:
            # Mix of deterministic and stochastic tasks
            if task_id == "T002":
                return random.uniform(5.0, 15.0)  # High variance
            elif task_id == "T003":
                return random.uniform(8.0, 12.0)  # Medium variance
            else:
                return {"T001": 5.0, "T004": 2.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
            TaskDistributionInput(task_id="T003", dependencies="T001"),
            TaskDistributionInput(task_id="T004", dependencies="T002,T003"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=200,
        )

        # Verify all components are present
        assert len(metrics.probabilistic_critical_path) > 0
        assert len(metrics.task_criticality) == 4
        assert len(metrics.risk_drivers) >= 0
        assert len(metrics.confidence_intervals) >= 3

        # Verify task criticality data completeness
        for task_id in ["T001", "T002", "T003", "T004"]:
            data = metrics.task_criticality[task_id]
            assert data.task_id == task_id
            assert 0.0 <= data.criticality_index <= 1.0
            assert data.times_critical >= 0
            assert data.total_iterations == 200
            assert data.mean_duration > 0.0
            assert data.duration_variance >= 0.0

    def test_integration_with_monte_carlo_engine(self):
        """Test RiskAnalyzer properly integrates with MonteCarloEngine."""
        monte_carlo = MonteCarloEngine(iterations=50)
        analyzer = RiskAnalyzer(monte_carlo_engine=monte_carlo)

        def sampler(task_id: str) -> float:
            return {"T001": 5.0, "T002": 3.0}[task_id]

        tasks = [
            TaskDistributionInput(task_id="T001", dependencies=""),
            TaskDistributionInput(task_id="T002", dependencies="T001"),
        ]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=50,
        )

        # Should have completed all 50 iterations
        for task_data in metrics.task_criticality.values():
            assert task_data.total_iterations == 50


class TestRiskAnalyzerEdgeCases:
    """Test edge cases and error handling."""

    def test_single_task_project(self):
        """Test risk analysis on single-task project."""
        analyzer = RiskAnalyzer()

        def sampler(task_id: str) -> float:
            return {"T001": 5.0}[task_id]

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=20,
        )

        # Single task is always critical
        assert metrics.task_criticality["T001"].criticality_index == 1.0
        assert "T001" in metrics.probabilistic_critical_path

    def test_empty_task_list(self):
        """Test handling of empty task list."""
        analyzer = RiskAnalyzer()

        def sampler(task_id: str) -> float:
            return 5.0

        tasks = []

        # Should raise ValueError for empty task list
        with pytest.raises(ValueError, match="empty"):
            analyzer.analyze_risk(
                tasks=tasks,
                duration_sampler=sampler,
                project_start=date(2025, 1, 13),
                num_iterations=10,
            )

    def test_invalid_iterations(self):
        """Test handling of invalid iteration count."""
        analyzer = RiskAnalyzer()

        def sampler(task_id: str) -> float:
            return 5.0

        tasks = [TaskDistributionInput(task_id="T001", dependencies="")]

        # Should raise ValueError for non-positive iterations
        with pytest.raises(ValueError):
            analyzer.analyze_risk(
                tasks=tasks,
                duration_sampler=sampler,
                project_start=date(2025, 1, 13),
                num_iterations=0,
            )

        with pytest.raises(ValueError):
            analyzer.analyze_risk(
                tasks=tasks,
                duration_sampler=sampler,
                project_start=date(2025, 1, 13),
                num_iterations=-10,
            )

    def test_large_project_performance(self):
        """Test risk analysis on larger project (performance check)."""
        analyzer = RiskAnalyzer()

        def sampler(task_id: str) -> float:
            return 5.0

        # Create 20-task project
        tasks = [
            TaskDistributionInput(task_id=f"T{i:03d}", dependencies="")
            for i in range(20)
        ]

        # Should complete in reasonable time
        metrics = analyzer.analyze_risk(
            tasks=tasks,
            duration_sampler=sampler,
            project_start=date(2025, 1, 13),
            num_iterations=100,
        )

        assert len(metrics.task_criticality) == 20
