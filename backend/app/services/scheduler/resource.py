"""
Resource management for project scheduling.

Handles resource definitions, resource pools, and resource availability tracking.
Supports person, equipment, and material resource types.
"""

from datetime import date
from enum import Enum
from typing import List, Optional, Set


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found in the pool."""

    pass


class ResourceType(Enum):
    """
    Types of resources that can be assigned to tasks.

    - PERSON: Human resources (developers, managers, etc.)
    - EQUIPMENT: Physical equipment (servers, tools, machinery)
    - MATERIAL: Consumable materials (concrete, supplies, etc.)
    """

    PERSON = "PERSON"
    EQUIPMENT = "EQUIPMENT"
    MATERIAL = "MATERIAL"


class Resource:
    """
    Represents a schedulable resource with capacity and availability.

    Resources can be people, equipment, or materials. Each resource has:
    - Unique identifier
    - Name for display
    - Type classification
    - Capacity (how much work it can handle simultaneously)
    - Availability calendar (dates when unavailable)

    Attributes:
        id: Unique resource identifier
        name: Human-readable resource name
        type: ResourceType classification
        capacity: Maximum simultaneous allocation (default 1.0)
        unavailable_dates: Set of dates when resource is unavailable
    """

    def __init__(
        self,
        id: str,
        name: str,
        type: ResourceType,
        capacity: float = 1.0,
        unavailable_dates: Optional[List[date]] = None,
    ):
        """
        Initialize resource.

        Args:
            id: Unique resource identifier
            name: Human-readable name
            type: Resource type (PERSON, EQUIPMENT, MATERIAL)
            capacity: Maximum simultaneous allocation (must be > 0)
            unavailable_dates: List of dates when resource is unavailable

        Raises:
            ValueError: If capacity is not positive
        """
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self.id = id
        self.name = name
        self.type = type
        self.capacity = capacity
        self.unavailable_dates: Set[date] = set(unavailable_dates or [])

    def is_available(self, check_date: date) -> bool:
        """
        Check if resource is available on specific date.

        Args:
            check_date: Date to check availability

        Returns:
            True if resource is available, False if unavailable
        """
        return check_date not in self.unavailable_dates

    def is_available_during(self, start_date: date, end_date: date) -> bool:
        """
        Check if resource is available for entire date range.

        Args:
            start_date: Start of date range
            end_date: End of date range (inclusive)

        Returns:
            True if available for all dates in range, False otherwise
        """
        current = start_date
        while current <= end_date:
            if not self.is_available(current):
                return False
            current += date.resolution
        return True

    def __repr__(self) -> str:
        """String representation of resource."""
        return f"Resource(id={self.id}, name={self.name}, type={self.type.value}, capacity={self.capacity})"


class ResourcePool:
    """
    Collection of resources available for project scheduling.

    Provides operations for:
    - Adding and removing resources
    - Querying resources by ID, type, or availability
    - Managing resource collections

    Attributes:
        _resources: Dictionary mapping resource ID to Resource object
    """

    def __init__(self) -> None:
        """Initialize empty resource pool."""
        self._resources: dict[str, Resource] = {}

    def add_resource(self, resource: Resource) -> None:
        """
        Add resource to pool.

        Args:
            resource: Resource to add

        Raises:
            ValueError: If resource with same ID already exists
        """
        if resource.id in self._resources:
            raise ValueError(f"Resource {resource.id} already exists in pool")

        self._resources[resource.id] = resource

    def remove_resource(self, resource_id: str) -> None:
        """
        Remove resource from pool.

        Args:
            resource_id: ID of resource to remove

        Raises:
            ResourceNotFoundError: If resource doesn't exist
        """
        if resource_id not in self._resources:
            raise ResourceNotFoundError(f"Resource {resource_id} not found in pool")

        del self._resources[resource_id]

    def get_resource(self, resource_id: str) -> Resource:
        """
        Get resource by ID.

        Args:
            resource_id: Resource identifier

        Returns:
            Resource object

        Raises:
            ResourceNotFoundError: If resource doesn't exist
        """
        if resource_id not in self._resources:
            raise ResourceNotFoundError(f"Resource {resource_id} not found in pool")

        return self._resources[resource_id]

    def has_resource(self, resource_id: str) -> bool:
        """
        Check if pool contains resource.

        Args:
            resource_id: Resource identifier to check

        Returns:
            True if resource exists in pool, False otherwise
        """
        return resource_id in self._resources

    def get_all_resources(self) -> List[Resource]:
        """
        Get all resources in pool.

        Returns:
            List of all Resource objects
        """
        return list(self._resources.values())

    def get_resources_by_type(self, resource_type: ResourceType) -> List[Resource]:
        """
        Get all resources of specific type.

        Args:
            resource_type: Type to filter by

        Returns:
            List of resources matching type
        """
        return [r for r in self._resources.values() if r.type == resource_type]

    def get_available_resources(self, check_date: date) -> List[Resource]:
        """
        Get resources available on specific date.

        Args:
            check_date: Date to check availability

        Returns:
            List of available resources on that date
        """
        return [r for r in self._resources.values() if r.is_available(check_date)]

    def size(self) -> int:
        """
        Get number of resources in pool.

        Returns:
            Count of resources
        """
        return len(self._resources)

    def is_empty(self) -> bool:
        """
        Check if pool is empty.

        Returns:
            True if pool has no resources, False otherwise
        """
        return len(self._resources) == 0

    def __repr__(self) -> str:
        """String representation of pool."""
        return f"ResourcePool(size={self.size()})"
