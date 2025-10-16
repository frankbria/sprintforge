"""
Tests for probability distribution classes used in Monte Carlo simulation.

Tests cover:
- Basic sampling functionality
- Statistical properties (mean approximation)
- Edge cases and boundary conditions
- Validation errors
- Randomness verification
"""

import numpy as np
import pytest
from pydantic import ValidationError

from app.services.scheduler.distributions import (
    NormalDistribution,
    TriangularDistribution,
    UniformDistribution,
)


class TestTriangularDistribution:
    """Tests for TriangularDistribution (PERT formula)."""

    def test_initialization_valid_values(self):
        """Test that valid values initialize correctly."""
        dist = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=8.0)
        assert dist.optimistic == 3.0
        assert dist.most_likely == 5.0
        assert dist.pessimistic == 8.0

    def test_initialization_equal_values(self):
        """Test initialization with equal values (deterministic case)."""
        dist = TriangularDistribution(optimistic=5.0, most_likely=5.0, pessimistic=5.0)
        assert dist.optimistic == 5.0
        assert dist.most_likely == 5.0
        assert dist.pessimistic == 5.0

    def test_initialization_invalid_order(self):
        """Test that invalid order raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TriangularDistribution(optimistic=8.0, most_likely=5.0, pessimistic=3.0)
        assert "optimistic" in str(exc_info.value).lower()

    def test_initialization_most_likely_less_than_optimistic(self):
        """Test that most_likely < optimistic raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TriangularDistribution(optimistic=5.0, most_likely=3.0, pessimistic=8.0)
        assert "most_likely" in str(exc_info.value).lower()

    def test_initialization_pessimistic_less_than_most_likely(self):
        """Test that pessimistic < most_likely raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TriangularDistribution(optimistic=3.0, most_likely=8.0, pessimistic=5.0)
        assert "pessimistic" in str(exc_info.value).lower()

    def test_initialization_negative_values(self):
        """Test that negative values raise validation error."""
        with pytest.raises(ValidationError):
            TriangularDistribution(optimistic=-1.0, most_likely=5.0, pessimistic=8.0)

    def test_mean_calculation(self):
        """Test PERT mean formula: (o + 4m + p) / 6."""
        dist = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=9.0)
        expected_mean = (3.0 + 4 * 5.0 + 9.0) / 6.0
        assert dist.mean() == pytest.approx(expected_mean)

    def test_mean_calculation_equal_values(self):
        """Test mean with equal values returns that value."""
        dist = TriangularDistribution(optimistic=5.0, most_likely=5.0, pessimistic=5.0)
        assert dist.mean() == 5.0

    def test_sample_returns_float(self):
        """Test that sample returns a float value."""
        dist = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=8.0)
        sample = dist.sample()
        assert isinstance(sample, float)

    def test_sample_within_bounds(self):
        """Test that samples are within [optimistic, pessimistic] bounds."""
        dist = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=8.0)
        samples = [dist.sample() for _ in range(1000)]
        assert all(3.0 <= s <= 8.0 for s in samples)

    def test_sample_deterministic_case(self):
        """Test sampling with equal values returns that value."""
        dist = TriangularDistribution(optimistic=5.0, most_likely=5.0, pessimistic=5.0)
        samples = [dist.sample() for _ in range(100)]
        assert all(s == 5.0 for s in samples)

    def test_sample_statistical_mean(self):
        """Test that sample mean approximates triangular distribution mean over many samples."""
        dist = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=9.0)
        samples = [dist.sample() for _ in range(10000)]
        sample_mean = np.mean(samples)
        # Triangular distribution mean is (a + b + c) / 3, not PERT mean
        expected_mean = (3.0 + 5.0 + 9.0) / 3.0
        # Allow 5% tolerance for statistical variation
        assert sample_mean == pytest.approx(expected_mean, rel=0.05)

    def test_sample_randomness(self):
        """Test that samples show randomness (variance)."""
        dist = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=8.0)
        samples = [dist.sample() for _ in range(100)]
        # Standard deviation should be > 0 for random samples
        assert np.std(samples) > 0

    def test_sample_different_seeds_produce_different_results(self):
        """Test that different random states produce different samples."""
        dist1 = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=8.0)
        dist2 = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=8.0)

        # Sample multiple times to reduce chance of collision
        samples1 = [dist1.sample() for _ in range(10)]
        samples2 = [dist2.sample() for _ in range(10)]

        # At least some samples should differ
        assert samples1 != samples2

    def test_sample_reproducibility_with_seed(self):
        """Test that setting random seed produces reproducible results."""
        np.random.seed(42)
        dist1 = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=8.0)
        samples1 = [dist1.sample() for _ in range(5)]

        np.random.seed(42)
        dist2 = TriangularDistribution(optimistic=3.0, most_likely=5.0, pessimistic=8.0)
        samples2 = [dist2.sample() for _ in range(5)]

        assert samples1 == samples2


class TestUniformDistribution:
    """Tests for UniformDistribution."""

    def test_initialization_valid_values(self):
        """Test that valid values initialize correctly."""
        dist = UniformDistribution(min_duration=2.0, max_duration=8.0)
        assert dist.min_duration == 2.0
        assert dist.max_duration == 8.0

    def test_initialization_invalid_order(self):
        """Test that max < min raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UniformDistribution(min_duration=8.0, max_duration=2.0)
        assert "min_duration" in str(exc_info.value).lower()

    def test_initialization_equal_values(self):
        """Test that min == max raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UniformDistribution(min_duration=5.0, max_duration=5.0)
        assert "min_duration" in str(exc_info.value).lower()

    def test_initialization_negative_values(self):
        """Test that negative values raise validation error."""
        with pytest.raises(ValidationError):
            UniformDistribution(min_duration=-1.0, max_duration=5.0)

    def test_mean_calculation(self):
        """Test uniform mean formula: (min + max) / 2."""
        dist = UniformDistribution(min_duration=2.0, max_duration=8.0)
        expected_mean = (2.0 + 8.0) / 2.0
        assert dist.mean() == expected_mean

    def test_sample_returns_float(self):
        """Test that sample returns a float value."""
        dist = UniformDistribution(min_duration=2.0, max_duration=8.0)
        sample = dist.sample()
        assert isinstance(sample, float)

    def test_sample_within_bounds(self):
        """Test that samples are within [min, max] bounds."""
        dist = UniformDistribution(min_duration=2.0, max_duration=8.0)
        samples = [dist.sample() for _ in range(1000)]
        assert all(2.0 <= s <= 8.0 for s in samples)

    def test_sample_statistical_mean(self):
        """Test that sample mean approximates uniform mean over many samples."""
        dist = UniformDistribution(min_duration=2.0, max_duration=8.0)
        samples = [dist.sample() for _ in range(10000)]
        sample_mean = np.mean(samples)
        expected_mean = dist.mean()
        # Allow 5% tolerance for statistical variation
        assert sample_mean == pytest.approx(expected_mean, rel=0.05)

    def test_sample_coverage(self):
        """Test that samples cover the full range uniformly."""
        dist = UniformDistribution(min_duration=0.0, max_duration=10.0)
        samples = [dist.sample() for _ in range(10000)]

        # Check that we have samples in different parts of the range
        bins = [0, 2.5, 5.0, 7.5, 10.0]
        hist, _ = np.histogram(samples, bins=bins)

        # Each bin should have roughly 25% of samples (within tolerance)
        expected_per_bin = 10000 / 4
        for count in hist:
            assert count == pytest.approx(expected_per_bin, rel=0.1)

    def test_sample_randomness(self):
        """Test that samples show randomness (variance)."""
        dist = UniformDistribution(min_duration=2.0, max_duration=8.0)
        samples = [dist.sample() for _ in range(100)]
        assert np.std(samples) > 0

    def test_sample_reproducibility_with_seed(self):
        """Test that setting random seed produces reproducible results."""
        np.random.seed(42)
        dist1 = UniformDistribution(min_duration=2.0, max_duration=8.0)
        samples1 = [dist1.sample() for _ in range(5)]

        np.random.seed(42)
        dist2 = UniformDistribution(min_duration=2.0, max_duration=8.0)
        samples2 = [dist2.sample() for _ in range(5)]

        assert samples1 == samples2


class TestNormalDistribution:
    """Tests for NormalDistribution with truncation at 0."""

    def test_initialization_valid_values(self):
        """Test that valid values initialize correctly."""
        dist = NormalDistribution(mean=5.0, std_dev=1.5)
        assert dist.mean == 5.0
        assert dist.std_dev == 1.5

    def test_initialization_zero_std_dev(self):
        """Test that zero std_dev raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            NormalDistribution(mean=5.0, std_dev=0.0)
        assert "std_dev" in str(exc_info.value).lower()

    def test_initialization_negative_std_dev(self):
        """Test that negative std_dev raises validation error."""
        with pytest.raises(ValidationError):
            NormalDistribution(mean=5.0, std_dev=-1.0)

    def test_initialization_negative_mean(self):
        """Test that negative mean raises validation error."""
        with pytest.raises(ValidationError):
            NormalDistribution(mean=-5.0, std_dev=1.5)

    def test_get_mean(self):
        """Test that get_mean returns the configured mean."""
        dist = NormalDistribution(mean=5.0, std_dev=1.5)
        assert dist.get_mean() == 5.0

    def test_sample_returns_float(self):
        """Test that sample returns a float value."""
        dist = NormalDistribution(mean=5.0, std_dev=1.5)
        sample = dist.sample()
        assert isinstance(sample, float)

    def test_sample_non_negative(self):
        """Test that samples are always >= 0 (truncated)."""
        dist = NormalDistribution(mean=1.0, std_dev=2.0)
        samples = [dist.sample() for _ in range(1000)]
        assert all(s >= 0.0 for s in samples)

    def test_sample_statistical_mean_well_above_zero(self):
        """Test sample mean approximates normal mean when mean >> 0."""
        dist = NormalDistribution(mean=10.0, std_dev=1.0)
        samples = [dist.sample() for _ in range(10000)]
        sample_mean = np.mean(samples)
        # Should be close to 10.0 since truncation is rare
        assert sample_mean == pytest.approx(10.0, rel=0.05)

    def test_sample_mean_shifts_when_truncated(self):
        """Test that sample mean shifts upward when truncation occurs frequently."""
        dist = NormalDistribution(mean=1.0, std_dev=2.0)
        samples = [dist.sample() for _ in range(10000)]
        sample_mean = np.mean(samples)
        # Mean should be > 1.0 due to truncation removing negative tail
        assert sample_mean > 1.0

    def test_sample_randomness(self):
        """Test that samples show randomness (variance)."""
        dist = NormalDistribution(mean=5.0, std_dev=1.5)
        samples = [dist.sample() for _ in range(100)]
        assert np.std(samples) > 0

    def test_sample_standard_deviation_approximation(self):
        """Test that sample std_dev approximates configured std_dev when no truncation."""
        dist = NormalDistribution(mean=20.0, std_dev=2.0)
        samples = [dist.sample() for _ in range(10000)]
        sample_std = np.std(samples)
        # Should be close to 2.0 since truncation is extremely rare
        assert sample_std == pytest.approx(2.0, rel=0.1)

    def test_sample_reproducibility_with_seed(self):
        """Test that setting random seed produces reproducible results."""
        np.random.seed(42)
        dist1 = NormalDistribution(mean=5.0, std_dev=1.5)
        samples1 = [dist1.sample() for _ in range(5)]

        np.random.seed(42)
        dist2 = NormalDistribution(mean=5.0, std_dev=1.5)
        samples2 = [dist2.sample() for _ in range(5)]

        assert samples1 == samples2

    def test_sample_truncation_active(self):
        """Test that truncation actually happens with mean close to zero."""
        dist = NormalDistribution(mean=0.5, std_dev=1.0)
        samples = [dist.sample() for _ in range(1000)]
        # All samples should be >= 0
        assert all(s >= 0.0 for s in samples)
        # Some samples should be small (close to 0) due to truncation
        assert any(s < 0.1 for s in samples)


class TestDistributionComparison:
    """Tests comparing behavior across different distributions."""

    def test_all_distributions_have_sample_method(self):
        """Test that all distributions implement sample()."""
        triangular = TriangularDistribution(
            optimistic=3.0, most_likely=5.0, pessimistic=8.0
        )
        uniform = UniformDistribution(min_duration=3.0, max_duration=8.0)
        normal = NormalDistribution(mean=5.5, std_dev=1.0)

        assert hasattr(triangular, "sample")
        assert hasattr(uniform, "sample")
        assert hasattr(normal, "sample")

    def test_distributions_with_similar_ranges_produce_similar_means(self):
        """Test that different distributions with similar params produce similar means."""
        triangular = TriangularDistribution(
            optimistic=3.0, most_likely=5.0, pessimistic=9.0
        )
        uniform = UniformDistribution(min_duration=3.0, max_duration=9.0)
        normal = NormalDistribution(mean=6.0, std_dev=1.5)

        # Sample many times
        tri_samples = [triangular.sample() for _ in range(10000)]
        uni_samples = [uniform.sample() for _ in range(10000)]
        norm_samples = [normal.sample() for _ in range(10000)]

        tri_mean = np.mean(tri_samples)
        uni_mean = np.mean(uni_samples)
        norm_mean = np.mean(norm_samples)

        # All means should be in the same ballpark (3-9 range)
        assert 4.0 <= tri_mean <= 7.0
        assert 5.0 <= uni_mean <= 7.0
        assert 5.0 <= norm_mean <= 7.0
