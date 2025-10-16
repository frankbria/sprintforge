"""
Tests for Resource management implementation.

Tests Resource, ResourceType enum, and ResourcePool classes using TDD approach.
"""

from datetime import date, timedelta

import pytest

from app.services.scheduler.resource import (
    Resource,
    ResourceNotFoundError,
    ResourcePool,
    ResourceType,
)


class TestResourceType:
    """Test ResourceType enum."""

    def test_resource_type_values(self):
        """Test that ResourceType has expected values."""
        assert ResourceType.PERSON.value == "PERSON"
        assert ResourceType.EQUIPMENT.value == "EQUIPMENT"
        assert ResourceType.MATERIAL.value == "MATERIAL"

    def test_resource_type_membership(self):
        """Test ResourceType membership checks."""
        assert ResourceType.PERSON in ResourceType
        assert ResourceType.EQUIPMENT in ResourceType
        assert ResourceType.MATERIAL in ResourceType


class TestResourceBasics:
    """Test basic Resource functionality."""

    def test_create_person_resource(self):
        """Test creating a person resource."""
        resource = Resource(
            id="R001",
            name="John Developer",
            type=ResourceType.PERSON,
            capacity=1.0,
        )

        assert resource.id == "R001"
        assert resource.name == "John Developer"
        assert resource.type == ResourceType.PERSON
        assert resource.capacity == 1.0

    def test_create_equipment_resource(self):
        """Test creating an equipment resource."""
        resource = Resource(
            id="E001",
            name="Server Rack",
            type=ResourceType.EQUIPMENT,
            capacity=5.0,
        )

        assert resource.id == "E001"
        assert resource.name == "Server Rack"
        assert resource.type == ResourceType.EQUIPMENT
        assert resource.capacity == 5.0

    def test_create_material_resource(self):
        """Test creating a material resource."""
        resource = Resource(
            id="M001",
            name="Concrete",
            type=ResourceType.MATERIAL,
            capacity=100.0,
        )

        assert resource.id == "M001"
        assert resource.name == "Concrete"
        assert resource.type == ResourceType.MATERIAL
        assert resource.capacity == 100.0

    def test_resource_default_capacity(self):
        """Test that resource defaults to capacity 1.0."""
        resource = Resource(
            id="R001",
            name="Developer",
            type=ResourceType.PERSON,
        )

        assert resource.capacity == 1.0

    def test_resource_negative_capacity_fails(self):
        """Test that negative capacity raises error."""
        with pytest.raises(ValueError, match="capacity must be positive"):
            Resource(
                id="R001",
                name="Developer",
                type=ResourceType.PERSON,
                capacity=-1.0,
            )

    def test_resource_zero_capacity_fails(self):
        """Test that zero capacity raises error."""
        with pytest.raises(ValueError, match="capacity must be positive"):
            Resource(
                id="R001",
                name="Developer",
                type=ResourceType.PERSON,
                capacity=0.0,
            )


class TestResourceAvailability:
    """Test resource availability functionality."""

    def test_resource_fully_available_by_default(self):
        """Test that resource is fully available by default."""
        resource = Resource(
            id="R001",
            name="Developer",
            type=ResourceType.PERSON,
        )

        # Check availability on arbitrary dates
        assert resource.is_available(date(2025, 1, 13)) is True
        assert resource.is_available(date(2025, 6, 15)) is True

    def test_resource_with_unavailable_dates(self):
        """Test resource with specified unavailable dates."""
        unavailable = [date(2025, 1, 15), date(2025, 1, 16)]
        resource = Resource(
            id="R001",
            name="Developer",
            type=ResourceType.PERSON,
            unavailable_dates=unavailable,
        )

        assert resource.is_available(date(2025, 1, 14)) is True
        assert resource.is_available(date(2025, 1, 15)) is False
        assert resource.is_available(date(2025, 1, 16)) is False
        assert resource.is_available(date(2025, 1, 17)) is True

    def test_resource_availability_with_date_range(self):
        """Test checking availability across date range."""
        unavailable = [date(2025, 1, 15)]
        resource = Resource(
            id="R001",
            name="Developer",
            type=ResourceType.PERSON,
            unavailable_dates=unavailable,
        )

        start = date(2025, 1, 13)
        end = date(2025, 1, 17)

        # Should return False because one day in range is unavailable
        assert resource.is_available_during(start, end) is False

    def test_resource_available_during_entire_range(self):
        """Test resource available during entire date range."""
        unavailable = [date(2025, 1, 10), date(2025, 1, 20)]
        resource = Resource(
            id="R001",
            name="Developer",
            type=ResourceType.PERSON,
            unavailable_dates=unavailable,
        )

        start = date(2025, 1, 13)
        end = date(2025, 1, 17)

        assert resource.is_available_during(start, end) is True


class TestResourcePool:
    """Test ResourcePool functionality."""

    def test_create_empty_pool(self):
        """Test creating empty resource pool."""
        pool = ResourcePool()

        assert pool.size() == 0
        assert pool.is_empty() is True

    def test_add_resource_to_pool(self):
        """Test adding resource to pool."""
        pool = ResourcePool()
        resource = Resource(
            id="R001",
            name="Developer",
            type=ResourceType.PERSON,
        )

        pool.add_resource(resource)

        assert pool.size() == 1
        assert pool.is_empty() is False

    def test_add_multiple_resources(self):
        """Test adding multiple resources to pool."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON)
        r2 = Resource(id="R002", name="Dev2", type=ResourceType.PERSON)
        r3 = Resource(id="E001", name="Server", type=ResourceType.EQUIPMENT)

        pool.add_resource(r1)
        pool.add_resource(r2)
        pool.add_resource(r3)

        assert pool.size() == 3

    def test_add_duplicate_resource_id_fails(self):
        """Test that adding duplicate resource ID raises error."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON)
        r2 = Resource(id="R001", name="Dev2", type=ResourceType.PERSON)

        pool.add_resource(r1)

        with pytest.raises(ValueError, match="Resource R001 already exists"):
            pool.add_resource(r2)

    def test_get_resource_by_id(self):
        """Test retrieving resource by ID."""
        pool = ResourcePool()
        resource = Resource(id="R001", name="Developer", type=ResourceType.PERSON)
        pool.add_resource(resource)

        retrieved = pool.get_resource("R001")

        assert retrieved.id == "R001"
        assert retrieved.name == "Developer"

    def test_get_nonexistent_resource_fails(self):
        """Test that getting nonexistent resource raises error."""
        pool = ResourcePool()

        with pytest.raises(ResourceNotFoundError, match="Resource R999 not found"):
            pool.get_resource("R999")

    def test_has_resource(self):
        """Test checking if pool has resource."""
        pool = ResourcePool()
        resource = Resource(id="R001", name="Developer", type=ResourceType.PERSON)
        pool.add_resource(resource)

        assert pool.has_resource("R001") is True
        assert pool.has_resource("R999") is False

    def test_remove_resource(self):
        """Test removing resource from pool."""
        pool = ResourcePool()
        resource = Resource(id="R001", name="Developer", type=ResourceType.PERSON)
        pool.add_resource(resource)

        assert pool.size() == 1

        pool.remove_resource("R001")

        assert pool.size() == 0
        assert pool.has_resource("R001") is False

    def test_remove_nonexistent_resource_fails(self):
        """Test that removing nonexistent resource raises error."""
        pool = ResourcePool()

        with pytest.raises(ResourceNotFoundError, match="Resource R999 not found"):
            pool.remove_resource("R999")

    def test_get_resources_by_type(self):
        """Test filtering resources by type."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON)
        r2 = Resource(id="R002", name="Dev2", type=ResourceType.PERSON)
        r3 = Resource(id="E001", name="Server", type=ResourceType.EQUIPMENT)
        r4 = Resource(id="M001", name="Concrete", type=ResourceType.MATERIAL)

        pool.add_resource(r1)
        pool.add_resource(r2)
        pool.add_resource(r3)
        pool.add_resource(r4)

        people = pool.get_resources_by_type(ResourceType.PERSON)
        equipment = pool.get_resources_by_type(ResourceType.EQUIPMENT)
        materials = pool.get_resources_by_type(ResourceType.MATERIAL)

        assert len(people) == 2
        assert len(equipment) == 1
        assert len(materials) == 1

    def test_get_available_resources_on_date(self):
        """Test getting resources available on specific date."""
        pool = ResourcePool()
        unavailable_date = date(2025, 1, 15)

        r1 = Resource(
            id="R001",
            name="Dev1",
            type=ResourceType.PERSON,
            unavailable_dates=[unavailable_date],
        )
        r2 = Resource(id="R002", name="Dev2", type=ResourceType.PERSON)

        pool.add_resource(r1)
        pool.add_resource(r2)

        # On unavailable date, only R002 available
        available = pool.get_available_resources(unavailable_date)
        assert len(available) == 1
        assert available[0].id == "R002"

        # On other dates, both available
        available = pool.get_available_resources(date(2025, 1, 14))
        assert len(available) == 2

    def test_get_all_resources(self):
        """Test getting all resources from pool."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON)
        r2 = Resource(id="R002", name="Dev2", type=ResourceType.PERSON)

        pool.add_resource(r1)
        pool.add_resource(r2)

        all_resources = pool.get_all_resources()

        assert len(all_resources) == 2
        assert all_resources[0].id in ["R001", "R002"]
        assert all_resources[1].id in ["R001", "R002"]


class TestResourcePoolEdgeCases:
    """Test edge cases for ResourcePool."""

    def test_pool_with_single_resource(self):
        """Test pool operations with single resource."""
        pool = ResourcePool()
        resource = Resource(id="R001", name="Developer", type=ResourceType.PERSON)

        pool.add_resource(resource)
        assert pool.size() == 1

        retrieved = pool.get_resource("R001")
        assert retrieved.id == "R001"

    def test_get_resources_by_type_empty_result(self):
        """Test getting resources by type with no matches."""
        pool = ResourcePool()
        r1 = Resource(id="R001", name="Dev1", type=ResourceType.PERSON)
        pool.add_resource(r1)

        equipment = pool.get_resources_by_type(ResourceType.EQUIPMENT)
        assert len(equipment) == 0

    def test_get_available_resources_all_unavailable(self):
        """Test getting available resources when all are unavailable."""
        pool = ResourcePool()
        unavailable_date = date(2025, 1, 15)

        r1 = Resource(
            id="R001",
            name="Dev1",
            type=ResourceType.PERSON,
            unavailable_dates=[unavailable_date],
        )
        r2 = Resource(
            id="R002",
            name="Dev2",
            type=ResourceType.PERSON,
            unavailable_dates=[unavailable_date],
        )

        pool.add_resource(r1)
        pool.add_resource(r2)

        available = pool.get_available_resources(unavailable_date)
        assert len(available) == 0
