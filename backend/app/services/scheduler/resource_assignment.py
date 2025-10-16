"""
Resource assignment and conflict detection for project scheduling.

Handles task resource requirements, allocations, and conflict detection.
Integrates with ResourcePool to validate resource availability and capacity.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from app.services.scheduler.resource import Resource, ResourcePool, ResourceType


class InsufficientResourceError(Exception):
    """Raised when required resources are not available."""

    pass


@dataclass
class TaskResourceRequirement:
    """
    Defines resource requirements for a task.

    Specifies what type and quantity of resources a task needs.
    Can optionally specify specific resource IDs for assignment.

    Attributes:
        task_id: Task requiring resources
        resource_type: Type of resource needed
        quantity: Amount of resource needed (e.g., 1.0 = full-time, 0.5 = half-time)
        resource_ids: Optional specific resource IDs to use
    """

    task_id: str
    resource_type: ResourceType
    quantity: float
    resource_ids: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Validate requirement after initialization."""
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


@dataclass
class ResourceAllocation:
    """
    Represents allocation of a resource to a task for a time period.

    Tracks which resource is assigned to which task, for how long,
    and how much of the resource's capacity is consumed.

    Attributes:
        task_id: Task receiving the allocation
        resource_id: Resource being allocated
        start_date: Allocation start date
        end_date: Allocation end date (inclusive)
        quantity: Amount of resource capacity allocated (1.0 = 100%)
    """

    task_id: str
    resource_id: str
    start_date: date
    end_date: date
    quantity: float

    def __post_init__(self) -> None:
        """Validate allocation after initialization."""
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

    def overlaps_with(self, other: "ResourceAllocation") -> bool:
        """
        Check if this allocation overlaps with another allocation.

        Two allocations overlap if they:
        1. Use the same resource
        2. Have overlapping time periods

        Args:
            other: Other allocation to check

        Returns:
            True if allocations overlap, False otherwise
        """
        if self.resource_id != other.resource_id:
            return False

        # Check if date ranges overlap
        # No overlap if one ends before the other starts
        if self.end_date < other.start_date or other.end_date < self.start_date:
            return False

        return True

    def __repr__(self) -> str:
        """String representation of allocation."""
        return (
            f"ResourceAllocation(task={self.task_id}, resource={self.resource_id}, "
            f"{self.start_date} to {self.end_date}, quantity={self.quantity})"
        )


@dataclass
class ResourceConflict:
    """
    Represents a resource allocation conflict.

    Occurs when:
    - Total allocation exceeds resource capacity
    - Resource is allocated when unavailable
    - Multiple conflicting requirements

    Attributes:
        resource_id: Resource with conflict
        task_ids: Tasks involved in conflict
        start_date: Conflict period start
        end_date: Conflict period end
        allocated_quantity: Total allocation during conflict
        capacity: Resource capacity
        reason: Description of conflict
    """

    resource_id: str
    task_ids: List[str]
    start_date: date
    end_date: date
    allocated_quantity: float
    capacity: float
    reason: str

    def overallocation_amount(self) -> float:
        """
        Calculate amount of overallocation.

        Returns:
            Difference between allocated quantity and capacity (>0 = overallocated)
        """
        return self.allocated_quantity - self.capacity

    def __repr__(self) -> str:
        """String representation of conflict."""
        return (
            f"ResourceConflict(resource={self.resource_id}, "
            f"tasks={self.task_ids}, {self.start_date} to {self.end_date}, "
            f"overallocation={self.overallocation_amount():.2f})"
        )


class ResourceConflictDetector:
    """
    Detects resource allocation conflicts.

    Analyzes resource allocations to identify:
    - Overallocation (exceeding resource capacity)
    - Unavailability conflicts (allocating unavailable resources)
    - Multi-task conflicts (same resource, multiple tasks)

    Attributes:
        resource_pool: Pool of available resources
    """

    def __init__(self, resource_pool: ResourcePool):
        """
        Initialize conflict detector.

        Args:
            resource_pool: Pool containing all resources
        """
        self.resource_pool = resource_pool

    def detect_conflicts(
        self, allocations: List[ResourceAllocation]
    ) -> List[ResourceConflict]:
        """
        Detect all conflicts in list of allocations.

        Checks for:
        1. Resource capacity violations (overallocation)
        2. Resource unavailability violations
        3. Overlapping allocations exceeding capacity

        Args:
            allocations: List of resource allocations to check

        Returns:
            List of detected conflicts (empty if no conflicts)
        """
        conflicts: List[ResourceConflict] = []

        if not allocations:
            return conflicts

        # Group allocations by resource
        allocations_by_resource: dict[str, List[ResourceAllocation]] = {}
        for alloc in allocations:
            if alloc.resource_id not in allocations_by_resource:
                allocations_by_resource[alloc.resource_id] = []
            allocations_by_resource[alloc.resource_id].append(alloc)

        # Check each resource for conflicts
        for resource_id, resource_allocations in allocations_by_resource.items():
            resource = self.resource_pool.get_resource(resource_id)

            # Check for unavailability conflicts
            unavail_conflicts = self._check_unavailability_conflicts(
                resource, resource_allocations
            )
            conflicts.extend(unavail_conflicts)

            # Check for overallocation conflicts
            overalloc_conflicts = self._check_overallocation_conflicts(
                resource, resource_allocations
            )
            conflicts.extend(overalloc_conflicts)

        return conflicts

    def _check_unavailability_conflicts(
        self, resource: Resource, allocations: List[ResourceAllocation]
    ) -> List[ResourceConflict]:
        """
        Check if resource is allocated when unavailable.

        Args:
            resource: Resource to check
            allocations: Allocations for this resource

        Returns:
            List of unavailability conflicts
        """
        conflicts = []

        for alloc in allocations:
            # Check if resource is available for entire allocation period
            if not resource.is_available_during(alloc.start_date, alloc.end_date):
                conflict = ResourceConflict(
                    resource_id=resource.id,
                    task_ids=[alloc.task_id],
                    start_date=alloc.start_date,
                    end_date=alloc.end_date,
                    allocated_quantity=alloc.quantity,
                    capacity=resource.capacity,
                    reason="Resource unavailable during allocation period",
                )
                conflicts.append(conflict)

        return conflicts

    def _check_overallocation_conflicts(
        self, resource: Resource, allocations: List[ResourceAllocation]
    ) -> List[ResourceConflict]:
        """
        Check if total allocation exceeds resource capacity.

        Finds overlapping allocations and checks if their combined
        quantity exceeds resource capacity.

        Args:
            resource: Resource to check
            allocations: Allocations for this resource

        Returns:
            List of overallocation conflicts
        """
        conflicts: List[ResourceConflict] = []

        # Check each pair of allocations for overlap and overallocation
        for i, alloc1 in enumerate(allocations):
            overlapping = [alloc1]

            # Find all allocations that overlap with alloc1
            for j, alloc2 in enumerate(allocations):
                if i != j and alloc1.overlaps_with(alloc2):
                    overlapping.append(alloc2)

            # If we have overlapping allocations, check total quantity
            if len(overlapping) > 1:
                total_quantity = sum(a.quantity for a in overlapping)

                if total_quantity > resource.capacity:
                    # Find conflict period (intersection of all overlapping periods)
                    conflict_start = max(a.start_date for a in overlapping)
                    conflict_end = min(a.end_date for a in overlapping)

                    # Check if we already reported this conflict
                    task_ids = sorted([a.task_id for a in overlapping])
                    conflict_exists = any(
                        c.resource_id == resource.id
                        and sorted(c.task_ids) == task_ids
                        and c.start_date == conflict_start
                        and c.end_date == conflict_end
                        for c in conflicts
                    )

                    if not conflict_exists:
                        conflict = ResourceConflict(
                            resource_id=resource.id,
                            task_ids=task_ids,
                            start_date=conflict_start,
                            end_date=conflict_end,
                            allocated_quantity=total_quantity,
                            capacity=resource.capacity,
                            reason="Overallocation",
                        )
                        conflicts.append(conflict)

        return conflicts

    def __repr__(self) -> str:
        """String representation of detector."""
        return f"ResourceConflictDetector(resources={self.resource_pool.size()})"
