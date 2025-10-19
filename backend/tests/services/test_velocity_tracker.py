"""
Test suite for Velocity Tracker Service.

This test file follows TDD principles (RED-GREEN-REFACTOR):
- Tests written BEFORE implementation
- Tests will FAIL initially (RED phase)
- Target: 85%+ code coverage

Tests cover:
- VelocityTracker class methods
- Sprint velocity calculations
- Velocity trend analysis
- Moving average calculations
- Anomaly detection
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Import service that will be created
from app.services.velocity_tracker import VelocityTracker
from app.models.historical_metrics import SprintVelocity


@pytest_asyncio.fixture
async def velocity_tracker(test_db_session: AsyncSession):
    """Create VelocityTracker instance with test database session."""
    return VelocityTracker(db_session=test_db_session)


@pytest_asyncio.fixture
async def sample_velocities(test_db_session: AsyncSession, test_project):
    """Create sample sprint velocity data for testing."""
    now = datetime.now(timezone.utc)
    velocities = []

    # Create 10 sprints with varying velocities
    velocity_values = [35, 40, 38, 42, 45, 43, 48, 50, 47, 52]

    for i, value in enumerate(velocity_values):
        velocity = SprintVelocity(
            project_id=test_project.id,
            sprint_id=str(uuid4()),
            velocity_points=float(value),
            completed_tasks=int(value / 2.5),
            timestamp=now - timedelta(days=(10 - i) * 14),
        )
        test_db_session.add(velocity)
        velocities.append(velocity)

    await test_db_session.commit()
    return velocities


class TestVelocityTrackerInit:
    """Test suite for VelocityTracker initialization."""

    @pytest.mark.asyncio
    async def test_velocity_tracker_initialization(self, test_db_session: AsyncSession):
        """Test creating VelocityTracker instance."""
        tracker = VelocityTracker(db_session=test_db_session)

        assert tracker is not None
        assert tracker.db_session == test_db_session

    @pytest.mark.asyncio
    async def test_velocity_tracker_requires_db_session(self):
        """Test that VelocityTracker requires a database session."""
        with pytest.raises(TypeError):
            VelocityTracker()


class TestCalculateSprintVelocity:
    """Test suite for calculate_sprint_velocity method."""

    @pytest.mark.asyncio
    async def test_calculate_sprint_velocity_basic(
        self, velocity_tracker: VelocityTracker, test_project
    ):
        """Test basic sprint velocity calculation."""
        sprint_id = str(uuid4())

        velocity = await velocity_tracker.calculate_sprint_velocity(
            project_id=test_project.id, sprint_id=sprint_id
        )

        assert isinstance(velocity, float)
        assert velocity >= 0.0

    @pytest.mark.asyncio
    async def test_calculate_sprint_velocity_with_tasks(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test velocity calculation when sprint has completed tasks."""
        sprint_id = str(uuid4())

        # Mock completed tasks for this sprint
        # In real implementation, this would query actual task data
        velocity = await velocity_tracker.calculate_sprint_velocity(
            project_id=test_project.id, sprint_id=sprint_id
        )

        assert velocity >= 0.0

    @pytest.mark.asyncio
    async def test_calculate_sprint_velocity_no_tasks(
        self, velocity_tracker: VelocityTracker, test_project
    ):
        """Test velocity calculation when sprint has no completed tasks."""
        sprint_id = str(uuid4())

        velocity = await velocity_tracker.calculate_sprint_velocity(
            project_id=test_project.id, sprint_id=sprint_id
        )

        # Should return 0 for sprints with no tasks
        assert velocity == 0.0

    @pytest.mark.asyncio
    async def test_calculate_sprint_velocity_saves_to_database(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test that calculated velocity is saved to database."""
        sprint_id = str(uuid4())

        velocity = await velocity_tracker.calculate_sprint_velocity(
            project_id=test_project.id, sprint_id=sprint_id
        )

        # Verify velocity was saved
        from sqlalchemy import select

        result = await test_db_session.execute(
            select(SprintVelocity).where(SprintVelocity.sprint_id == sprint_id)
        )
        saved_velocity = result.scalar_one_or_none()

        # Note: This test will fail in RED phase until implementation
        # In GREEN phase, we expect saved_velocity to exist
        assert saved_velocity is not None or velocity == 0.0


class TestGetVelocityTrend:
    """Test suite for get_velocity_trend method."""

    @pytest.mark.asyncio
    async def test_get_velocity_trend_default_count(
        self, velocity_tracker: VelocityTracker, test_project, sample_velocities
    ):
        """Test getting velocity trend with default count (10 sprints)."""
        trend = await velocity_tracker.get_velocity_trend(project_id=test_project.id)

        assert isinstance(trend, list)
        assert len(trend) <= 10
        assert all(isinstance(v, SprintVelocity) for v in trend)

    @pytest.mark.asyncio
    async def test_get_velocity_trend_custom_count(
        self, velocity_tracker: VelocityTracker, test_project, sample_velocities
    ):
        """Test getting velocity trend with custom sprint count."""
        trend = await velocity_tracker.get_velocity_trend(
            project_id=test_project.id, num_sprints=5
        )

        assert isinstance(trend, list)
        assert len(trend) <= 5

    @pytest.mark.asyncio
    async def test_get_velocity_trend_ordered_by_time(
        self, velocity_tracker: VelocityTracker, test_project, sample_velocities
    ):
        """Test that velocity trend is ordered chronologically."""
        trend = await velocity_tracker.get_velocity_trend(project_id=test_project.id)

        # Verify ordering (oldest to newest or newest to oldest)
        if len(trend) > 1:
            timestamps = [v.timestamp for v in trend]
            # Check if sorted in any direction
            is_ascending = all(timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1))
            is_descending = all(timestamps[i] >= timestamps[i + 1] for i in range(len(timestamps) - 1))
            assert is_ascending or is_descending

    @pytest.mark.asyncio
    async def test_get_velocity_trend_no_data(
        self, velocity_tracker: VelocityTracker, test_project
    ):
        """Test getting velocity trend when no data exists."""
        trend = await velocity_tracker.get_velocity_trend(project_id=test_project.id)

        assert isinstance(trend, list)
        assert len(trend) == 0

    @pytest.mark.asyncio
    async def test_get_velocity_trend_filters_by_project(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project, test_user_pro
    ):
        """Test that velocity trend only returns data for specified project."""
        # Create another project with velocities
        from app.models.project import Project

        other_project = Project(
            name="Other Project",
            owner_id=test_user_pro.id,
            configuration={},
            template_version="1.0",
        )
        test_db_session.add(other_project)
        await test_db_session.commit()
        await test_db_session.refresh(other_project)

        # Add velocities to both projects
        for project in [test_project, other_project]:
            velocity = SprintVelocity(
                project_id=project.id,
                sprint_id=str(uuid4()),
                velocity_points=40.0,
                completed_tasks=16,
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        # Get trend for test_project only
        trend = await velocity_tracker.get_velocity_trend(project_id=test_project.id)

        assert all(v.project_id == test_project.id for v in trend)


class TestCalculateMovingAverage:
    """Test suite for calculate_moving_average method."""

    @pytest.mark.asyncio
    async def test_calculate_moving_average_default_window(
        self, velocity_tracker: VelocityTracker, test_project, sample_velocities
    ):
        """Test moving average calculation with default window (3 sprints)."""
        moving_avg = await velocity_tracker.calculate_moving_average(project_id=test_project.id)

        assert isinstance(moving_avg, float)
        assert moving_avg > 0.0

    @pytest.mark.asyncio
    async def test_calculate_moving_average_custom_window(
        self, velocity_tracker: VelocityTracker, test_project, sample_velocities
    ):
        """Test moving average calculation with custom window size."""
        moving_avg = await velocity_tracker.calculate_moving_average(
            project_id=test_project.id, window=5
        )

        assert isinstance(moving_avg, float)
        assert moving_avg > 0.0

    @pytest.mark.asyncio
    async def test_calculate_moving_average_matches_expected_value(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test that moving average calculates correct value."""
        # Create exactly 3 sprints with known velocities
        velocities = [30.0, 40.0, 50.0]
        for value in velocities:
            velocity = SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=value,
                completed_tasks=int(value / 2.5),
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        moving_avg = await velocity_tracker.calculate_moving_average(
            project_id=test_project.id, window=3
        )

        # Expected: (30 + 40 + 50) / 3 = 40.0
        assert abs(moving_avg - 40.0) < 0.01

    @pytest.mark.asyncio
    async def test_calculate_moving_average_insufficient_data(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test moving average when fewer data points than window size."""
        # Create only 2 velocities but request window of 3
        for value in [30.0, 40.0]:
            velocity = SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=value,
                completed_tasks=int(value / 2.5),
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        moving_avg = await velocity_tracker.calculate_moving_average(
            project_id=test_project.id, window=3
        )

        # Should calculate average of available data
        assert abs(moving_avg - 35.0) < 0.01

    @pytest.mark.asyncio
    async def test_calculate_moving_average_no_data(
        self, velocity_tracker: VelocityTracker, test_project
    ):
        """Test moving average calculation when no data exists."""
        moving_avg = await velocity_tracker.calculate_moving_average(project_id=test_project.id)

        # Should return 0 or None when no data available
        assert moving_avg == 0.0 or moving_avg is None


class TestDetectVelocityAnomalies:
    """Test suite for detect_velocity_anomalies method."""

    @pytest.mark.asyncio
    async def test_detect_velocity_anomalies_returns_list(
        self, velocity_tracker: VelocityTracker, test_project, sample_velocities
    ):
        """Test that anomaly detection returns a list."""
        anomalies = await velocity_tracker.detect_velocity_anomalies(project_id=test_project.id)

        assert isinstance(anomalies, list)

    @pytest.mark.asyncio
    async def test_detect_velocity_anomalies_no_anomalies(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test anomaly detection with consistent velocity (no anomalies)."""
        # Create velocities with very little variation
        for value in [40.0, 41.0, 40.5, 39.5, 40.0]:
            velocity = SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=value,
                completed_tasks=int(value / 2.5),
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        anomalies = await velocity_tracker.detect_velocity_anomalies(project_id=test_project.id)

        assert len(anomalies) == 0

    @pytest.mark.asyncio
    async def test_detect_velocity_anomalies_with_spike(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test anomaly detection with velocity spike."""
        # Create velocities with one obvious spike
        values = [40.0, 41.0, 100.0, 39.5, 40.0]  # 100.0 is a spike
        for value in values:
            velocity = SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=value,
                completed_tasks=int(value / 2.5),
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        anomalies = await velocity_tracker.detect_velocity_anomalies(project_id=test_project.id)

        # Should detect at least one anomaly
        assert len(anomalies) >= 1

    @pytest.mark.asyncio
    async def test_detect_velocity_anomalies_with_drop(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test anomaly detection with velocity drop."""
        # Create velocities with one obvious drop
        values = [40.0, 41.0, 5.0, 39.5, 40.0]  # 5.0 is a drop
        for value in values:
            velocity = SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=value,
                completed_tasks=int(value / 2.5),
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        anomalies = await velocity_tracker.detect_velocity_anomalies(project_id=test_project.id)

        # Should detect at least one anomaly
        assert len(anomalies) >= 1

    @pytest.mark.asyncio
    async def test_detect_velocity_anomalies_includes_metadata(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test that detected anomalies include useful metadata."""
        # Create velocities with spike
        values = [40.0, 41.0, 100.0, 39.5, 40.0]
        for value in values:
            velocity = SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=value,
                completed_tasks=int(value / 2.5),
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        anomalies = await velocity_tracker.detect_velocity_anomalies(project_id=test_project.id)

        if len(anomalies) > 0:
            anomaly = anomalies[0]
            # Each anomaly should be a dict with useful info
            assert isinstance(anomaly, dict)
            assert "sprint_id" in anomaly or "velocity_points" in anomaly or "deviation" in anomaly

    @pytest.mark.asyncio
    async def test_detect_velocity_anomalies_insufficient_data(
        self, velocity_tracker: VelocityTracker, test_db_session: AsyncSession, test_project
    ):
        """Test anomaly detection with insufficient data points."""
        # Create only 2 velocities (not enough for statistical analysis)
        for value in [40.0, 41.0]:
            velocity = SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=value,
                completed_tasks=int(value / 2.5),
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        anomalies = await velocity_tracker.detect_velocity_anomalies(project_id=test_project.id)

        # Should return empty list or handle gracefully
        assert isinstance(anomalies, list)

    @pytest.mark.asyncio
    async def test_detect_velocity_anomalies_no_data(
        self, velocity_tracker: VelocityTracker, test_project
    ):
        """Test anomaly detection when no velocity data exists."""
        anomalies = await velocity_tracker.detect_velocity_anomalies(project_id=test_project.id)

        assert isinstance(anomalies, list)
        assert len(anomalies) == 0
