"""
Tests for SimulationResult model.

Following TDD approach: Write tests first (RED), then implement (GREEN), then refactor.
Target: ≥85% coverage, 100% pass rate.
"""

import pytest
from datetime import datetime, date
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.simulation_result import SimulationResult
from app.models.user import User
from app.models.project import Project


@pytest.fixture
async def test_user(test_db_session: AsyncSession) -> User:
    """Create test user for simulation relationships."""
    user = User(
        id=uuid4(),
        email=f"test_{uuid4()}@example.com",
        name="Test User",
        subscription_tier="pro",
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_project(test_db_session: AsyncSession, test_user: User) -> Project:
    """Create test project for simulation relationships."""
    project = Project(
        id=uuid4(),
        name="Test Project",
        description="Test project for simulations",
        owner_id=test_user.id,
        configuration={},
    )
    test_db_session.add(project)
    await test_db_session.commit()
    await test_db_session.refresh(project)
    return project


class TestSimulationResultModel:
    """Test SimulationResult model creation and validation."""

    async def test_create_simulation_result(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test creating a basic simulation result."""
        simulation = SimulationResult(
            project_id=test_project.id,
            user_id=test_user.id,
            iterations=10000,
            task_count=15,
            project_start_date=date(2025, 1, 13),
            mean_duration=52.3,
            median_duration=51.5,
            std_deviation=4.8,
            confidence_intervals={10: 45.2, 50: 51.5, 90: 61.5, 95: 65.0, 99: 72.1},
            simulation_duration_seconds=2.5,
        )

        test_db_session.add(simulation)
        await test_db_session.commit()
        await test_db_session.refresh(simulation)

        # Verify creation
        assert simulation.id is not None
        assert simulation.project_id == test_project.id
        assert simulation.user_id == test_user.id
        assert simulation.iterations == 10000
        assert simulation.task_count == 15
        assert simulation.mean_duration == 52.3
        assert simulation.median_duration == 51.5
        assert simulation.std_deviation == 4.8
        assert len(simulation.confidence_intervals) == 5
        assert simulation.confidence_intervals[50] == 51.5
        assert simulation.simulation_duration_seconds == 2.5
        assert simulation.created_at is not None
        assert isinstance(simulation.created_at, datetime)

    async def test_simulation_result_required_fields(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test that required fields are enforced."""
        simulation = SimulationResult(
            project_id=test_project.id,
            user_id=test_user.id,
            iterations=1000,
            task_count=10,
            project_start_date=date(2025, 1, 13),
            mean_duration=50.0,
            median_duration=50.0,
            std_deviation=3.0,
            confidence_intervals={50: 50.0},
        )

        test_db_session.add(simulation)
        await test_db_session.commit()

        # Should succeed with all required fields
        assert simulation.id is not None

    async def test_simulation_result_relationships(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test relationships to User and Project."""
        simulation = SimulationResult(
            project_id=test_project.id,
            user_id=test_user.id,
            iterations=5000,
            task_count=20,
            project_start_date=date(2025, 1, 13),
            mean_duration=75.0,
            median_duration=74.5,
            std_deviation=6.2,
            confidence_intervals={10: 65.0, 50: 74.5, 90: 85.0},
        )

        test_db_session.add(simulation)
        await test_db_session.commit()
        await test_db_session.refresh(simulation)

        # Test relationships
        assert simulation.project is not None
        assert simulation.project.id == test_project.id
        assert simulation.project.name == "Test Project"

        assert simulation.user is not None
        assert simulation.user.id == test_user.id
        assert simulation.user.email == test_user.email

    async def test_simulation_result_json_confidence_intervals(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test JSON storage of confidence intervals."""
        complex_intervals = {
            1: 40.1,
            5: 42.3,
            10: 45.2,
            25: 48.7,
            50: 51.5,
            75: 54.8,
            90: 61.5,
            95: 65.0,
            99: 72.1,
        }

        simulation = SimulationResult(
            project_id=test_project.id,
            user_id=test_user.id,
            iterations=50000,
            task_count=30,
            project_start_date=date(2025, 2, 1),
            mean_duration=52.3,
            median_duration=51.5,
            std_deviation=4.8,
            confidence_intervals=complex_intervals,
        )

        test_db_session.add(simulation)
        await test_db_session.commit()
        await test_db_session.refresh(simulation)

        # Verify JSON roundtrip
        assert simulation.confidence_intervals == complex_intervals
        assert simulation.confidence_intervals[99] == 72.1
        assert len(simulation.confidence_intervals) == 9

    async def test_simulation_result_created_at_index(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test that created_at is indexed for efficient queries."""
        # Create multiple simulations with different timestamps
        simulations = []
        for i in range(3):
            sim = SimulationResult(
                project_id=test_project.id,
                user_id=test_user.id,
                iterations=1000 * (i + 1),
                task_count=10,
                project_start_date=date(2025, 1, 13),
                mean_duration=50.0 + i,
                median_duration=50.0 + i,
                std_deviation=3.0,
                confidence_intervals={50: 50.0 + i},
            )
            test_db_session.add(sim)
            simulations.append(sim)

        await test_db_session.commit()

        # Query by created_at (descending) should work efficiently
        result = await test_db_session.execute(
            select(SimulationResult)
            .where(SimulationResult.project_id == test_project.id)
            .order_by(SimulationResult.created_at.desc())
        )
        results = result.scalars().all()

        # Verify ordering (most recent first)
        assert len(results) >= 3
        for i in range(len(results) - 1):
            assert results[i].created_at >= results[i + 1].created_at

    async def test_simulation_result_optional_duration_field(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test that simulation_duration_seconds is optional."""
        simulation = SimulationResult(
            project_id=test_project.id,
            user_id=test_user.id,
            iterations=1000,
            task_count=5,
            project_start_date=date(2025, 1, 13),
            mean_duration=30.0,
            median_duration=29.5,
            std_deviation=2.1,
            confidence_intervals={50: 29.5},
            # simulation_duration_seconds intentionally omitted
        )

        test_db_session.add(simulation)
        await test_db_session.commit()
        await test_db_session.refresh(simulation)

        assert simulation.id is not None
        assert simulation.simulation_duration_seconds is None

    async def test_multiple_simulations_for_project(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test storing multiple simulation results for same project."""
        simulations = []
        for i in range(5):
            sim = SimulationResult(
                project_id=test_project.id,
                user_id=test_user.id,
                iterations=10000,
                task_count=15 + i,
                project_start_date=date(2025, 1, 13),
                mean_duration=50.0 + i,
                median_duration=49.5 + i,
                std_deviation=4.0 + i * 0.1,
                confidence_intervals={10: 45.0 + i, 50: 49.5 + i, 90: 60.0 + i},
            )
            test_db_session.add(sim)
            simulations.append(sim)

        await test_db_session.commit()

        # Query all simulations for project
        result = await test_db_session.execute(
            select(SimulationResult).where(
                SimulationResult.project_id == test_project.id
            )
        )
        project_simulations = result.scalars().all()

        assert len(project_simulations) >= 5
        # Verify they all belong to the same project
        for sim in project_simulations:
            assert sim.project_id == test_project.id

    async def test_simulation_result_cascade_delete_with_project(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test that simulation results are deleted when project is deleted."""
        simulation = SimulationResult(
            project_id=test_project.id,
            user_id=test_user.id,
            iterations=1000,
            task_count=10,
            project_start_date=date(2025, 1, 13),
            mean_duration=50.0,
            median_duration=50.0,
            std_deviation=3.0,
            confidence_intervals={50: 50.0},
        )

        test_db_session.add(simulation)
        await test_db_session.commit()
        sim_id = simulation.id

        # Delete project
        await test_db_session.delete(test_project)
        await test_db_session.commit()

        # Verify simulation was cascade deleted
        result = await test_db_session.execute(
            select(SimulationResult).where(SimulationResult.id == sim_id)
        )
        deleted_sim = result.scalar_one_or_none()
        assert deleted_sim is None


class TestSimulationResultIndexes:
    """Test database indexes for query performance."""

    async def test_project_id_index(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test that project_id is indexed for efficient lookups."""
        # Create simulation
        simulation = SimulationResult(
            project_id=test_project.id,
            user_id=test_user.id,
            iterations=1000,
            task_count=10,
            project_start_date=date(2025, 1, 13),
            mean_duration=50.0,
            median_duration=50.0,
            std_deviation=3.0,
            confidence_intervals={50: 50.0},
        )

        test_db_session.add(simulation)
        await test_db_session.commit()

        # Query by project_id should use index
        result = await test_db_session.execute(
            select(SimulationResult).where(
                SimulationResult.project_id == test_project.id
            )
        )
        simulations = result.scalars().all()
        assert len(simulations) >= 1

    async def test_user_id_index(
        self, test_db_session: AsyncSession, test_project: Project, test_user: User
    ):
        """Test that user_id is indexed for efficient lookups."""
        # Create simulation
        simulation = SimulationResult(
            project_id=test_project.id,
            user_id=test_user.id,
            iterations=1000,
            task_count=10,
            project_start_date=date(2025, 1, 13),
            mean_duration=50.0,
            median_duration=50.0,
            std_deviation=3.0,
            confidence_intervals={50: 50.0},
        )

        test_db_session.add(simulation)
        await test_db_session.commit()

        # Query by user_id should use index
        result = await test_db_session.execute(
            select(SimulationResult).where(SimulationResult.user_id == test_user.id)
        )
        simulations = result.scalars().all()
        assert len(simulations) >= 1
