"""
Task sampling layer that integrates probability distributions with tasks.

Provides TaskSampler class that:
- Takes task configuration with distribution parameters
- Supports triangular, uniform, and normal distributions
- Samples duration values for Monte Carlo simulation
- Maintains task metadata (ID, dependencies)
"""

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.services.scheduler.distributions import (
    NormalDistribution,
    ProbabilityDistribution,
    TriangularDistribution,
    UniformDistribution,
)


class TaskDistributionInput(BaseModel):
    """
    Task configuration with probability distribution parameters.

    Supports three distribution types:
    - triangular: Requires optimistic, most_likely, pessimistic
    - uniform: Requires min_duration, max_duration
    - normal: Requires mean, std_dev

    Attributes:
        task_id: Unique task identifier (non-empty string)
        distribution_type: Type of probability distribution
        optimistic: Best case estimate (triangular only)
        most_likely: Most likely value (triangular only)
        pessimistic: Worst case estimate (triangular only)
        min_duration: Minimum duration (uniform only)
        max_duration: Maximum duration (uniform only)
        mean: Mean duration (normal only)
        std_dev: Standard deviation (normal only)
        dependencies: Comma-separated list of predecessor task IDs
    """

    task_id: str = Field(min_length=1, description="Unique task identifier")
    distribution_type: Literal["triangular", "uniform", "normal"] = Field(
        description="Type of probability distribution"
    )

    # Triangular distribution parameters
    optimistic: Optional[float] = Field(
        None, ge=0.0, description="Best case estimate (triangular)"
    )
    most_likely: Optional[float] = Field(
        None, ge=0.0, description="Most likely value (triangular)"
    )
    pessimistic: Optional[float] = Field(
        None, ge=0.0, description="Worst case estimate (triangular)"
    )

    # Uniform distribution parameters
    min_duration: Optional[float] = Field(
        None, ge=0.0, description="Minimum duration (uniform)"
    )
    max_duration: Optional[float] = Field(
        None, gt=0.0, description="Maximum duration (uniform)"
    )

    # Normal distribution parameters
    mean: Optional[float] = Field(None, ge=0.0, description="Mean duration (normal)")
    std_dev: Optional[float] = Field(
        None, gt=0.0, description="Standard deviation (normal)"
    )

    # Task metadata
    dependencies: str = Field(
        default="", description="Comma-separated predecessor task IDs"
    )

    @field_validator("task_id")
    @classmethod
    def validate_task_id_not_empty(cls, v: str) -> str:
        """Ensure task_id is not empty after stripping."""
        if not v or not v.strip():
            raise ValueError("task_id cannot be empty")
        return v

    def model_post_init(self, __context) -> None:
        """
        Validate that required parameters are present for the distribution type.

        Raises:
            ValueError: If required parameters are missing for the distribution type
        """
        if self.distribution_type == "triangular":
            if self.optimistic is None:
                raise ValueError(
                    "triangular distribution requires 'optimistic' parameter"
                )
            if self.most_likely is None:
                raise ValueError(
                    "triangular distribution requires 'most_likely' parameter"
                )
            if self.pessimistic is None:
                raise ValueError(
                    "triangular distribution requires 'pessimistic' parameter"
                )
            # Validate ordering
            if not (self.optimistic <= self.most_likely <= self.pessimistic):
                raise ValueError(
                    f"Invalid triangular parameters: optimistic ({self.optimistic}) "
                    f"<= most_likely ({self.most_likely}) <= pessimistic ({self.pessimistic})"
                )

        elif self.distribution_type == "uniform":
            if self.min_duration is None:
                raise ValueError(
                    "uniform distribution requires 'min_duration' parameter"
                )
            if self.max_duration is None:
                raise ValueError(
                    "uniform distribution requires 'max_duration' parameter"
                )
            # Validate range
            if self.min_duration >= self.max_duration:
                raise ValueError(
                    f"Invalid uniform parameters: min_duration ({self.min_duration}) "
                    f"must be < max_duration ({self.max_duration})"
                )

        elif self.distribution_type == "normal":
            if self.mean is None:
                raise ValueError("normal distribution requires 'mean' parameter")
            if self.std_dev is None:
                raise ValueError("normal distribution requires 'std_dev' parameter")
            # std_dev validation is handled by Field(gt=0.0)


class TaskSampler:
    """
    Samples task durations from configured probability distributions.

    Integrates probability distributions with task metadata to support
    Monte Carlo simulation of project schedules.

    Attributes:
        task: Task configuration with distribution parameters
        distribution: Underlying probability distribution object
    """

    def __init__(self, task: TaskDistributionInput):
        """
        Initialize TaskSampler with task configuration.

        Args:
            task: Task configuration with distribution parameters

        Raises:
            ValueError: If task configuration is invalid
        """
        self.task = task
        self.distribution = self._create_distribution()

    def _create_distribution(self) -> ProbabilityDistribution:
        """
        Create appropriate distribution object based on task configuration.

        Returns:
            Probability distribution object

        Raises:
            ValueError: If distribution type is unsupported or parameters are invalid
        """
        if self.task.distribution_type == "triangular":
            return TriangularDistribution(
                optimistic=self.task.optimistic,  # type: ignore
                most_likely=self.task.most_likely,  # type: ignore
                pessimistic=self.task.pessimistic,  # type: ignore
            )
        elif self.task.distribution_type == "uniform":
            return UniformDistribution(
                min_duration=self.task.min_duration,  # type: ignore
                max_duration=self.task.max_duration,  # type: ignore
            )
        elif self.task.distribution_type == "normal":
            return NormalDistribution(
                mean=self.task.mean,  # type: ignore
                std_dev=self.task.std_dev,  # type: ignore
            )
        else:
            raise ValueError(
                f"Unsupported distribution type: {self.task.distribution_type}"
            )

    def sample_duration(self) -> float:
        """
        Generate a random duration sample from the task's distribution.

        Returns:
            Sampled duration value (always non-negative)
        """
        return self.distribution.sample()

    def get_task_id(self) -> str:
        """
        Get the task identifier.

        Returns:
            Task ID string
        """
        return self.task.task_id

    def get_dependencies(self) -> str:
        """
        Get the task dependencies string.

        Returns:
            Comma-separated list of predecessor task IDs
        """
        return self.task.dependencies

    def get_distribution_type(self) -> str:
        """
        Get the distribution type for this task.

        Returns:
            Distribution type string ("triangular", "uniform", or "normal")
        """
        return self.task.distribution_type
