"""
Tests for Resource Assignment implementation.

Tests TaskResourceRequirement, ResourceAllocation, and ResourceConflictDetector classes.
"""

from datetime import date, timedelta

import pytest

from app.services.scheduler.resource import Resource, ResourcePool, ResourceType
from app.services.scheduler.resource_assignment import (
    InsufficientResourceError,
    ResourceAllocation,
    ResourceConflict,
    ResourceConflictDetector,
    TaskResourceRequirement,
)
from app.services.scheduler.work_calendar import WorkCalendar


class TestTaskResourceRequirement:
    """Test TaskResourceRequirement functionality."""

    def test_create_requirement(self):
        """Test creating task resource requirement."""
        req = TaskResourceRequirement(
            task_id="T001",
            resource_type=ResourceType.PERSON,
            quantity=2.0,
        )

        assert req.task_id == "T001"
        assert req.resource_type == ResourceType.PERSON
        assert req.quantity == 2.0
        assert req.resource_ids is None

    def test_create_requirement_with_specific_resources(self):
        """Test creating requirement with specific resource IDs."""
        req = TaskResourceRequirement(
            task_id="T001",
            resource_type=ResourceType.PERSON,
            quantity=1.0,
            resource_ids=["R001", "R002"],
        )

        assert req.resource_ids == ["R001", "R002"]

    def test_requirement_negative_quantity_fails(self):
        """Test that negative quantity raises error."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            TaskResourceRequirement(
                task_id="T001",
                resource_type=ResourceType.PERSON,
                quantity=-1.0,
            )

    def test_requirement_zero_quantity_fails(self):
        """Test that zero quantity raises error."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            TaskResourceRequirement(
                task_id="T001",
                resource_type=ResourceType.PERSON,
                quantity=0.0,
            )

    def test_requirement_fractional_quantity(self):
        """Test requirement with fractional quantity (partial allocation)."""
        req = TaskResourceRequirement(
            task_id="T001",
            resource_type=ResourceType.PERSON,
            quantity=0.5,  # Half-time allocation
        )

        assert req.quantity == 0.5


class TestResourceAllocation:
    """Test ResourceAllocation functionality."""

    def test_create_allocation(self):
        """Test creating resource allocation."""
        alloc = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )

        assert alloc.task_id == "T001"
        assert alloc.resource_id == "R001"
        assert alloc.start_date == date(2025, 1, 13)
        assert alloc.end_date == date(2025, 1, 17)
        assert alloc.quantity == 1.0

    def test_allocation_fractional_quantity(self):
        """Test allocation with fractional quantity."""
        alloc = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=0.5,
        )

        assert alloc.quantity == 0.5

    def test_allocation_end_before_start_fails(self):
        """Test that end date before start date raises error."""
        with pytest.raises(ValueError, match="end_date must be >= start_date"):
            ResourceAllocation(
                task_id="T001",
                resource_id="R001",
                start_date=date(2025, 1, 17),
                end_date=date(2025, 1, 13),
                quantity=1.0,
            )

    def test_allocation_negative_quantity_fails(self):
        """Test that negative quantity raises error."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            ResourceAllocation(
                task_id="T001",
                resource_id="R001",
                start_date=date(2025, 1, 13),
                end_date=date(2025, 1, 17),
                quantity=-1.0,
            )

    def test_allocation_overlaps_with_same_period(self):
        """Test checking if two allocations overlap (same period)."""
        alloc1 = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )
        alloc2 = ResourceAllocation(
            task_id="T002",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )

        assert alloc1.overlaps_with(alloc2) is True

    def test_allocation_overlaps_partial(self):
        """Test checking if allocations overlap partially."""
        alloc1 = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )
        alloc2 = ResourceAllocation(
            task_id="T002",
            resource_id="R001",
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 20),
            quantity=1.0,
        )

        assert alloc1.overlaps_with(alloc2) is True
        assert alloc2.overlaps_with(alloc1) is True

    def test_allocation_no_overlap(self):
        """Test allocations that don't overlap."""
        alloc1 = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )
        alloc2 = ResourceAllocation(
            task_id="T002",
            resource_id="R001",
            start_date=date(2025, 1, 20),
            end_date=date(2025, 1, 24),
            quantity=1.0,
        )

        assert alloc1.overlaps_with(alloc2) is False
        assert alloc2.overlaps_with(alloc1) is False

    def test_allocation_adjacent_periods_no_overlap(self):
        """Test that adjacent periods don't count as overlap."""
        alloc1 = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )
        alloc2 = ResourceAllocation(
            task_id="T002",
            resource_id="R001",
            start_date=date(2025, 1, 18),
            end_date=date(2025, 1, 24),
            quantity=1.0,
        )

        assert alloc1.overlaps_with(alloc2) is False


class TestResourceConflictDetector:
    """Test ResourceConflictDetector functionality."""

    def test_create_conflict_detector(self):
        """Test creating conflict detector."""
        pool = ResourcePool()
        detector = ResourceConflictDetector(pool)

        assert detector is not None

    def test_detect_no_conflicts_empty(self):
        """Test detecting conflicts with no allocations."""
        pool = ResourcePool()
        detector = ResourceConflictDetector(pool)

        conflicts = detector.detect_conflicts([])

        assert len(conflicts) == 0

    def test_detect_no_conflicts_single_allocation(self):
        """Test detecting conflicts with single allocation."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON, capacity=1.0)
        pool.add_resource(r1)

        detector = ResourceConflictDetector(pool)

        alloc = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )

        conflicts = detector.detect_conflicts([alloc])

        assert len(conflicts) == 0

    def test_detect_overallocation_conflict(self):
        """Test detecting overallocation conflict."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON, capacity=1.0)
        pool.add_resource(r1)

        detector = ResourceConflictDetector(pool)

        # Two tasks both want 100% of same resource at same time
        alloc1 = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )
        alloc2 = ResourceAllocation(
            task_id="T002",
            resource_id="R001",
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 20),
            quantity=1.0,
        )

        conflicts = detector.detect_conflicts([alloc1, alloc2])

        assert len(conflicts) == 1
        assert conflicts[0].resource_id == "R001"
        assert conflicts[0].allocated_quantity == 2.0  # Both allocations
        assert conflicts[0].capacity == 1.0

    def test_detect_partial_allocation_no_conflict(self):
        """Test that partial allocations within capacity have no conflict."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON, capacity=1.0)
        pool.add_resource(r1)

        detector = ResourceConflictDetector(pool)

        # Two tasks each want 50% - total 100%, no conflict
        alloc1 = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=0.5,
        )
        alloc2 = ResourceAllocation(
            task_id="T002",
            resource_id="R001",
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 20),
            quantity=0.5,
        )

        conflicts = detector.detect_conflicts([alloc1, alloc2])

        assert len(conflicts) == 0

    def test_detect_multiple_resource_conflicts(self):
        """Test detecting conflicts across multiple resources."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON, capacity=1.0)
        r2 = Resource(id="R002", name="Dev2", type=ResourceType.PERSON, capacity=1.0)
        pool.add_resource(r1)
        pool.add_resource(r2)

        detector = ResourceConflictDetector(pool)

        # Overallocate both resources
        allocations = [
            ResourceAllocation(
                "T001", "R001", date(2025, 1, 13), date(2025, 1, 17), 1.0
            ),
            ResourceAllocation(
                "T002", "R001", date(2025, 1, 15), date(2025, 1, 20), 1.0
            ),
            ResourceAllocation(
                "T003", "R002", date(2025, 1, 13), date(2025, 1, 17), 1.0
            ),
            ResourceAllocation(
                "T004", "R002", date(2025, 1, 15), date(2025, 1, 20), 1.0
            ),
        ]

        conflicts = detector.detect_conflicts(allocations)

        assert len(conflicts) == 2

    def test_detect_unavailable_resource_conflict(self):
        """Test detecting conflict when resource is unavailable."""
        unavailable_dates = [date(2025, 1, 15), date(2025, 1, 16)]
        pool = ResourcePool()
        r1 = Resource(
            id="R001",
            name="Dev1",
            type=ResourceType.PERSON,
            capacity=1.0,
            unavailable_dates=unavailable_dates,
        )
        pool.add_resource(r1)

        detector = ResourceConflictDetector(pool)

        alloc = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),  # Spans unavailable dates
            quantity=1.0,
        )

        conflicts = detector.detect_conflicts([alloc])

        assert len(conflicts) == 1
        assert "unavailable" in conflicts[0].reason.lower()


class TestResourceConflict:
    """Test ResourceConflict data structure."""

    def test_create_conflict(self):
        """Test creating resource conflict."""
        conflict = ResourceConflict(
            resource_id="R001",
            task_ids=["T001", "T002"],
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 17),
            allocated_quantity=2.0,
            capacity=1.0,
            reason="Overallocation",
        )

        assert conflict.resource_id == "R001"
        assert conflict.task_ids == ["T001", "T002"]
        assert conflict.allocated_quantity == 2.0
        assert conflict.capacity == 1.0

    def test_conflict_overallocation_amount(self):
        """Test calculating overallocation amount."""
        conflict = ResourceConflict(
            resource_id="R001",
            task_ids=["T001", "T002"],
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 17),
            allocated_quantity=2.5,
            capacity=1.0,
            reason="Overallocation",
        )

        assert conflict.overallocation_amount() == 1.5


class TestResourceAllocationIntegration:
    """Test resource allocation integration with WorkCalendar."""

    def test_allocate_resources_for_task(self):
        """Test allocating resources for task with calendar integration."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON)
        pool.add_resource(r1)

        calendar = WorkCalendar()
        detector = ResourceConflictDetector(pool)

        # Allocate resource for task spanning working days
        alloc = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),  # Monday
            end_date=date(2025, 1, 17),  # Friday
            quantity=1.0,
        )

        # Should have no conflicts
        conflicts = detector.detect_conflicts([alloc])
        assert len(conflicts) == 0

    def test_allocate_resources_respects_holidays(self):
        """Test that resource allocation considers holidays."""
        holidays = [date(2025, 1, 15)]  # Wednesday holiday
        calendar = WorkCalendar(holidays=holidays)

        pool = ResourcePool()
        r1 = Resource(
            id="R001",
            name="Dev1",
            type=ResourceType.PERSON,
            unavailable_dates=holidays,
        )
        pool.add_resource(r1)

        detector = ResourceConflictDetector(pool)

        # Allocate over holiday
        alloc = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=1.0,
        )

        conflicts = detector.detect_conflicts([alloc])
        assert len(conflicts) == 1


class TestResourceAssignmentEdgeCases:
    """Test edge cases for resource assignment."""

    def test_single_day_allocation(self):
        """Test allocation for single day."""
        alloc = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 13),
            quantity=1.0,
        )

        assert alloc.start_date == alloc.end_date

    def test_very_small_fractional_allocation(self):
        """Test very small fractional allocation (0.1 = 10%)."""
        alloc = ResourceAllocation(
            task_id="T001",
            resource_id="R001",
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 17),
            quantity=0.1,
        )

        assert alloc.quantity == 0.1

    def test_high_capacity_resource(self):
        """Test resource with high capacity (e.g., material)."""
        pool = ResourcePool()
        r1 = Resource(
            id="M001", name="Concrete", type=ResourceType.MATERIAL, capacity=1000.0
        )
        pool.add_resource(r1)

        detector = ResourceConflictDetector(pool)

        # Multiple allocations within capacity
        allocations = [
            ResourceAllocation(
                "T001", "M001", date(2025, 1, 13), date(2025, 1, 17), 300.0
            ),
            ResourceAllocation(
                "T002", "M001", date(2025, 1, 15), date(2025, 1, 20), 500.0
            ),
        ]

        conflicts = detector.detect_conflicts(allocations)
        assert len(conflicts) == 0  # 800 total < 1000 capacity
