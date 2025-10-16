"""
Tests for TaskSampler that integrates probability distributions with tasks.

Tests cover:
- TaskDistributionInput model validation
- Sampling from each distribution type
- Parameter validation for each distribution
- Multiple samples produce different results (randomness)
- Integration with task dependencies
- Edge cases and error conditions
"""

import numpy as np
import pytest
from pydantic import ValidationError

from app.services.scheduler.task_sampler import TaskDistributionInput, TaskSampler


class TestTaskDistributionInput:
    """Tests for TaskDistributionInput Pydantic model."""

    def test_triangular_distribution_valid(self):
        """Test valid triangular distribution parameters."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=3.0,
            most_likely=5.0,
            pessimistic=8.0,
            dependencies="",
        )
        assert task.task_id == "T001"
        assert task.distribution_type == "triangular"
        assert task.optimistic == 3.0
        assert task.most_likely == 5.0
        assert task.pessimistic == 8.0
        assert task.dependencies == ""

    def test_uniform_distribution_valid(self):
        """Test valid uniform distribution parameters."""
        task = TaskDistributionInput(
            task_id="T002",
            distribution_type="uniform",
            min_duration=2.0,
            max_duration=8.0,
            dependencies="T001",
        )
        assert task.task_id == "T002"
        assert task.distribution_type == "uniform"
        assert task.min_duration == 2.0
        assert task.max_duration == 8.0
        assert task.dependencies == "T001"

    def test_normal_distribution_valid(self):
        """Test valid normal distribution parameters."""
        task = TaskDistributionInput(
            task_id="T003",
            distribution_type="normal",
            mean=5.0,
            std_dev=1.5,
            dependencies="T001,T002",
        )
        assert task.task_id == "T003"
        assert task.distribution_type == "normal"
        assert task.mean == 5.0
        assert task.std_dev == 1.5
        assert task.dependencies == "T001,T002"

    def test_invalid_distribution_type(self):
        """Test that invalid distribution type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TaskDistributionInput(
                task_id="T001",
                distribution_type="gaussian",  # Invalid
                mean=5.0,
                std_dev=1.5,
            )
        assert "distribution_type" in str(exc_info.value).lower()

    def test_triangular_missing_parameters(self):
        """Test triangular distribution with missing parameters."""
        # Missing most_likely
        with pytest.raises(ValueError) as exc_info:
            task = TaskDistributionInput(
                task_id="T001",
                distribution_type="triangular",
                optimistic=3.0,
                pessimistic=8.0,
            )
        assert "most_likely" in str(exc_info.value).lower()

    def test_uniform_missing_parameters(self):
        """Test uniform distribution with missing parameters."""
        # Missing max_duration
        with pytest.raises(ValueError) as exc_info:
            task = TaskDistributionInput(
                task_id="T001", distribution_type="uniform", min_duration=2.0
            )
        assert "max_duration" in str(exc_info.value).lower()

    def test_normal_missing_parameters(self):
        """Test normal distribution with missing parameters."""
        # Missing std_dev
        with pytest.raises(ValueError) as exc_info:
            task = TaskDistributionInput(
                task_id="T001", distribution_type="normal", mean=5.0
            )
        assert "std_dev" in str(exc_info.value).lower()

    def test_triangular_invalid_parameter_order(self):
        """Test triangular with invalid parameter ordering."""
        with pytest.raises(ValueError) as exc_info:
            task = TaskDistributionInput(
                task_id="T001",
                distribution_type="triangular",
                optimistic=8.0,
                most_likely=5.0,
                pessimistic=3.0,
            )
        # Validation should catch this

    def test_uniform_invalid_range(self):
        """Test uniform with max <= min."""
        with pytest.raises(ValueError) as exc_info:
            task = TaskDistributionInput(
                task_id="T001",
                distribution_type="uniform",
                min_duration=8.0,
                max_duration=2.0,
            )

    def test_normal_invalid_std_dev(self):
        """Test normal with negative std_dev."""
        with pytest.raises(ValueError) as exc_info:
            task = TaskDistributionInput(
                task_id="T001", distribution_type="normal", mean=5.0, std_dev=-1.0
            )

    def test_negative_durations(self):
        """Test that negative duration parameters raise errors."""
        with pytest.raises(ValidationError):
            TaskDistributionInput(
                task_id="T001",
                distribution_type="triangular",
                optimistic=-1.0,
                most_likely=5.0,
                pessimistic=8.0,
            )

    def test_empty_task_id(self):
        """Test that empty task_id raises validation error."""
        with pytest.raises(ValidationError):
            TaskDistributionInput(
                task_id="",
                distribution_type="triangular",
                optimistic=3.0,
                most_likely=5.0,
                pessimistic=8.0,
            )

    def test_default_dependencies(self):
        """Test that dependencies defaults to empty string."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=3.0,
            most_likely=5.0,
            pessimistic=8.0,
        )
        assert task.dependencies == ""


class TestTaskSampler:
    """Tests for TaskSampler class."""

    def test_sample_triangular_distribution(self):
        """Test sampling from triangular distribution."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=3.0,
            most_likely=5.0,
            pessimistic=8.0,
        )
        sampler = TaskSampler(task)
        sample = sampler.sample_duration()

        assert isinstance(sample, float)
        assert 3.0 <= sample <= 8.0

    def test_sample_uniform_distribution(self):
        """Test sampling from uniform distribution."""
        task = TaskDistributionInput(
            task_id="T002",
            distribution_type="uniform",
            min_duration=2.0,
            max_duration=10.0,
        )
        sampler = TaskSampler(task)
        sample = sampler.sample_duration()

        assert isinstance(sample, float)
        assert 2.0 <= sample <= 10.0

    def test_sample_normal_distribution(self):
        """Test sampling from normal distribution."""
        task = TaskDistributionInput(
            task_id="T003", distribution_type="normal", mean=5.0, std_dev=1.5
        )
        sampler = TaskSampler(task)
        sample = sampler.sample_duration()

        assert isinstance(sample, float)
        assert sample >= 0.0  # Truncated at 0

    def test_multiple_samples_show_randomness(self):
        """Test that multiple samples are different (show randomness)."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=3.0,
            most_likely=5.0,
            pessimistic=8.0,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(100)]

        # Should have variance
        assert np.std(samples) > 0
        # Should have different values
        assert len(set(samples)) > 10

    def test_triangular_samples_within_bounds(self):
        """Test that triangular samples stay within bounds over many iterations."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=3.0,
            most_likely=5.0,
            pessimistic=8.0,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(1000)]

        assert all(3.0 <= s <= 8.0 for s in samples)

    def test_uniform_samples_within_bounds(self):
        """Test that uniform samples stay within bounds over many iterations."""
        task = TaskDistributionInput(
            task_id="T002",
            distribution_type="uniform",
            min_duration=2.0,
            max_duration=10.0,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(1000)]

        assert all(2.0 <= s <= 10.0 for s in samples)

    def test_normal_samples_non_negative(self):
        """Test that normal samples are always non-negative."""
        task = TaskDistributionInput(
            task_id="T003",
            distribution_type="normal",
            mean=1.0,
            std_dev=2.0,  # Large std_dev to test truncation
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(1000)]

        assert all(s >= 0.0 for s in samples)

    def test_triangular_statistical_mean(self):
        """Test that triangular samples approximate expected mean."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=3.0,
            most_likely=5.0,
            pessimistic=9.0,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(10000)]
        sample_mean = np.mean(samples)

        # Triangular distribution mean is (a + b + c) / 3
        expected_mean = (3.0 + 5.0 + 9.0) / 3.0
        assert sample_mean == pytest.approx(expected_mean, rel=0.05)

    def test_uniform_statistical_mean(self):
        """Test that uniform samples approximate expected mean."""
        task = TaskDistributionInput(
            task_id="T002",
            distribution_type="uniform",
            min_duration=2.0,
            max_duration=8.0,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(10000)]
        sample_mean = np.mean(samples)

        expected_mean = (2.0 + 8.0) / 2.0
        assert sample_mean == pytest.approx(expected_mean, rel=0.05)

    def test_normal_statistical_mean(self):
        """Test that normal samples approximate expected mean when mean >> 0."""
        task = TaskDistributionInput(
            task_id="T003", distribution_type="normal", mean=10.0, std_dev=1.0
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(10000)]
        sample_mean = np.mean(samples)

        # Should be close to 10.0 since truncation is rare
        assert sample_mean == pytest.approx(10.0, rel=0.05)

    def test_task_with_dependencies(self):
        """Test that task with dependencies can be sampled."""
        task = TaskDistributionInput(
            task_id="T003",
            distribution_type="triangular",
            optimistic=2.0,
            most_likely=4.0,
            pessimistic=6.0,
            dependencies="T001,T002",
        )
        sampler = TaskSampler(task)
        sample = sampler.sample_duration()

        assert isinstance(sample, float)
        assert 2.0 <= sample <= 6.0
        # Verify dependencies are preserved
        assert sampler.task.dependencies == "T001,T002"

    def test_deterministic_triangular(self):
        """Test triangular with equal values (deterministic case)."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=5.0,
            most_likely=5.0,
            pessimistic=5.0,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(100)]

        # All samples should be exactly 5.0
        assert all(s == 5.0 for s in samples)

    def test_get_task_id(self):
        """Test that sampler can return task_id."""
        task = TaskDistributionInput(
            task_id="TASK-123",
            distribution_type="uniform",
            min_duration=2.0,
            max_duration=8.0,
        )
        sampler = TaskSampler(task)
        assert sampler.get_task_id() == "TASK-123"

    def test_get_dependencies(self):
        """Test that sampler can return dependencies."""
        task = TaskDistributionInput(
            task_id="T003",
            distribution_type="triangular",
            optimistic=2.0,
            most_likely=4.0,
            pessimistic=6.0,
            dependencies="T001,T002",
        )
        sampler = TaskSampler(task)
        assert sampler.get_dependencies() == "T001,T002"

    def test_reproducibility_with_seed(self):
        """Test that setting random seed produces reproducible samples."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=3.0,
            most_likely=5.0,
            pessimistic=8.0,
        )

        np.random.seed(42)
        sampler1 = TaskSampler(task)
        samples1 = [sampler1.sample_duration() for _ in range(5)]

        np.random.seed(42)
        sampler2 = TaskSampler(task)
        samples2 = [sampler2.sample_duration() for _ in range(5)]

        assert samples1 == samples2

    def test_multiple_tasks_independent_sampling(self):
        """Test that multiple task samplers work independently."""
        task1 = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=1.0,
            most_likely=2.0,
            pessimistic=3.0,
        )
        task2 = TaskDistributionInput(
            task_id="T002",
            distribution_type="uniform",
            min_duration=5.0,
            max_duration=10.0,
        )

        sampler1 = TaskSampler(task1)
        sampler2 = TaskSampler(task2)

        sample1 = sampler1.sample_duration()
        sample2 = sampler2.sample_duration()

        # Samples from different ranges
        assert 1.0 <= sample1 <= 3.0
        assert 5.0 <= sample2 <= 10.0

    def test_get_distribution_type(self):
        """Test that sampler can return distribution type."""
        task = TaskDistributionInput(
            task_id="T001", distribution_type="normal", mean=5.0, std_dev=1.0
        )
        sampler = TaskSampler(task)
        assert sampler.get_distribution_type() == "normal"


class TestTaskSamplerEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_very_small_durations(self):
        """Test sampling with very small duration values."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="uniform",
            min_duration=0.1,
            max_duration=0.5,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(100)]

        assert all(0.1 <= s <= 0.5 for s in samples)

    def test_very_large_durations(self):
        """Test sampling with very large duration values."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="triangular",
            optimistic=100.0,
            most_likely=200.0,
            pessimistic=300.0,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(100)]

        assert all(100.0 <= s <= 300.0 for s in samples)

    def test_normal_with_large_std_dev(self):
        """Test normal distribution with std_dev larger than mean."""
        task = TaskDistributionInput(
            task_id="T001", distribution_type="normal", mean=2.0, std_dev=5.0
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(1000)]

        # All samples should still be non-negative due to truncation
        assert all(s >= 0.0 for s in samples)

    def test_uniform_narrow_range(self):
        """Test uniform distribution with very narrow range."""
        task = TaskDistributionInput(
            task_id="T001",
            distribution_type="uniform",
            min_duration=5.0,
            max_duration=5.1,
        )
        sampler = TaskSampler(task)
        samples = [sampler.sample_duration() for _ in range(100)]

        assert all(5.0 <= s <= 5.1 for s in samples)
        # Still should show some variance
        assert len(set(samples)) > 5

    def test_complex_dependencies_string(self):
        """Test task with complex dependency string."""
        task = TaskDistributionInput(
            task_id="T010",
            distribution_type="triangular",
            optimistic=2.0,
            most_likely=4.0,
            pessimistic=6.0,
            dependencies="T001,T002,T003,T004,T005",
        )
        sampler = TaskSampler(task)

        assert sampler.get_dependencies() == "T001,T002,T003,T004,T005"
        # Should still sample correctly
        sample = sampler.sample_duration()
        assert 2.0 <= sample <= 6.0
