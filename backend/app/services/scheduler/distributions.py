"""
Probability distribution classes for Monte Carlo simulation.

Provides three distribution types:
- TriangularDistribution: PERT formula (o + 4m + p) / 6
- UniformDistribution: Uniform distribution over [min, max]
- NormalDistribution: Normal distribution with truncation at 0
"""

from typing import Protocol

import numpy as np
from pydantic import BaseModel, Field, ValidationInfo, field_validator


class ProbabilityDistribution(Protocol):
    """Protocol defining the interface for probability distributions."""

    def sample(self) -> float:
        """Generate a single random sample from the distribution."""
        ...

    def mean(self) -> float:
        """Return the expected mean of the distribution."""
        ...


class TriangularDistribution(BaseModel):
    """
    Triangular distribution using PERT formula.

    PERT formula: mean = (optimistic + 4 * most_likely + pessimistic) / 6

    Attributes:
        optimistic: Best case estimate (minimum value)
        most_likely: Most likely value (mode)
        pessimistic: Worst case estimate (maximum value)
    """

    optimistic: float = Field(ge=0.0, description="Best case estimate (minimum)")
    most_likely: float = Field(ge=0.0, description="Most likely value (mode)")
    pessimistic: float = Field(ge=0.0, description="Worst case estimate (maximum)")

    @field_validator("most_likely")
    @classmethod
    def validate_most_likely(cls, v: float, info: ValidationInfo) -> float:
        """Ensure most_likely >= optimistic."""
        if "optimistic" in info.data and v < info.data["optimistic"]:
            raise ValueError(
                f"most_likely ({v}) must be >= optimistic ({info.data['optimistic']})"
            )
        return v

    @field_validator("pessimistic")
    @classmethod
    def validate_pessimistic(cls, v: float, info: ValidationInfo) -> float:
        """Ensure pessimistic >= most_likely."""
        if "most_likely" in info.data and v < info.data["most_likely"]:
            raise ValueError(
                f"pessimistic ({v}) must be >= most_likely ({info.data['most_likely']})"
            )
        return v

    def mean(self) -> float:
        """
        Calculate PERT expected value.

        Formula: (optimistic + 4 * most_likely + pessimistic) / 6
        """
        return (self.optimistic + 4 * self.most_likely + self.pessimistic) / 6.0

    def sample(self) -> float:
        """
        Generate a random sample from triangular distribution.

        Uses numpy's triangular distribution with left=optimistic,
        mode=most_likely, right=pessimistic.

        For deterministic cases (all values equal), returns that value.
        """
        # Handle deterministic case (all values equal)
        if self.optimistic == self.most_likely == self.pessimistic:
            return self.optimistic

        return float(
            np.random.triangular(
                left=self.optimistic, mode=self.most_likely, right=self.pessimistic
            )
        )


class UniformDistribution(BaseModel):
    """
    Uniform distribution over [min_duration, max_duration].

    All values in the range are equally likely.

    Attributes:
        min_duration: Minimum duration value
        max_duration: Maximum duration value
    """

    min_duration: float = Field(ge=0.0, description="Minimum duration")
    max_duration: float = Field(gt=0.0, description="Maximum duration")

    @field_validator("max_duration")
    @classmethod
    def validate_max_greater_than_min(cls, v: float, info: ValidationInfo) -> float:
        """Ensure max_duration > min_duration."""
        if "min_duration" in info.data:
            if v <= info.data["min_duration"]:
                min_val = info.data["min_duration"]
                raise ValueError(
                    f"max_duration ({v}) must be > min_duration ({min_val})"
                )
        return v

    def mean(self) -> float:
        """
        Calculate uniform distribution mean.

        Formula: (min_duration + max_duration) / 2
        """
        return (self.min_duration + self.max_duration) / 2.0

    def sample(self) -> float:
        """
        Generate a random sample from uniform distribution.

        Uses numpy's uniform distribution.
        """
        return float(np.random.uniform(low=self.min_duration, high=self.max_duration))


class NormalDistribution(BaseModel):
    """
    Normal distribution with truncation at 0.

    Negative samples are resampled until a non-negative value is obtained.
    This ensures task durations are always positive.

    Attributes:
        mean: Mean of the normal distribution
        std_dev: Standard deviation (must be > 0)
    """

    mean: float = Field(ge=0.0, description="Mean of the distribution")
    std_dev: float = Field(gt=0.0, description="Standard deviation")

    def get_mean(self) -> float:
        """Return the configured mean value."""
        return self.mean

    def sample(self) -> float:
        """
        Generate a random sample from truncated normal distribution.

        Samples are drawn from N(mean, std_dev^2) and truncated at 0.
        Negative values are clipped to 0.
        """
        sample = np.random.normal(loc=self.mean, scale=self.std_dev)
        # Truncate at 0 to ensure non-negative durations
        return float(max(0.0, sample))
