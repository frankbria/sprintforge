"""
Unit tests for AnalyticsService.

Tests cover all 5 core functions with comprehensive edge cases, mocking, and performance benchmarks.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch
import json
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics_service import AnalyticsService, AnalyticsError
from app.models.project import Project
from app.models.simulation_result import SimulationResult


@pytest.fixture
def mock_project():
    """Create a mock project with sample task configuration."""
    project_id = uuid4()
    return Project(
        id=project_id,
        name="Test Project",
        description="Test project for analytics",
        owner_id=uuid4(),
        configuration={
            "tasks": [
                {
                    "id": "T1",
                    "duration": 5.0,
                    "dependencies": [],
                    "resources": ["R1", "R2"],
                    "status": "completed",
                },
                {
                    "id": "T2",
                    "duration": 10.0,
                    "dependencies": ["T1"],
                    "resources": ["R1"],
                    "status": "completed",
                },
                {
                    "id": "T3",
                    "duration": 7.0,
                    "dependencies": ["T1"],
                    "resources": ["R3"],
                    "status": "in_progress",
                },
                {
                    "id": "T4",
                    "duration": 3.0,
                    "dependencies": ["T2", "T3"],
                    "resources": ["R2"],
                    "status": "pending",
                },
            ],
            "resources": {
                "R1": {"name": "Resource 1"},
                "R2": {"name": "Resource 2"},
                "R3": {"name": "Resource 3"},
            },
        },
        created_at=datetime.now() - timedelta(days=10),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_simulation_result():
    """Create a mock simulation result."""
    return SimulationResult(
        id=1,
        project_id=uuid4(),
        user_id=uuid4(),
        iterations=1000,
        task_count=4,
        project_start_date=date.today(),
        mean_duration=25.5,
        median_duration=25.0,
        std_deviation=3.2,
        confidence_intervals={
            10: 20.5,
            50: 25.0,
            75: 28.0,
            90: 30.5,
            95: 32.0,
        },
        created_at=datetime.now(),
        simulation_duration_seconds=0.5,
    )


@pytest.fixture
def analytics_service():
    """Create analytics service instance with caching disabled for testing."""
    return AnalyticsService(cache_ttl=0)


class TestAnalyticsServiceInitialization:
    """Test AnalyticsService initialization and Redis connection."""

    def test_init_default_ttl(self):
        """Test service initialization with default cache TTL."""
        service = AnalyticsService()
        assert service.cache_ttl == 300
        assert service._redis_client is None

    def test_init_custom_ttl(self):
        """Test service initialization with custom cache TTL."""
        service = AnalyticsService(cache_ttl=600)
        assert service.cache_ttl == 600

    @pytest.mark.asyncio
    async def test_get_redis_connection_failure(self):
        """Test Redis connection failure handling."""
        service = AnalyticsService()
        with patch("app.services.analytics_service.redis.from_url", side_effect=Exception("Connection failed")):
            redis_client = await service._get_redis()
            assert redis_client is None


class TestCalculateProjectHealthScore:
    """Test calculate_project_health_score function."""

    @pytest.mark.asyncio
    async def test_health_score_with_simulation(
        self, analytics_service, mock_project, mock_simulation_result
    ):
        """Test health score calculation with simulation data."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock database queries
        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = mock_project

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = mock_simulation_result

        mock_db.execute.side_effect = [project_result, sim_result]

        # Mock helper methods
        with patch.object(
            analytics_service, "_calculate_schedule_adherence_score", return_value=80.0
        ), patch.object(
            analytics_service, "_calculate_critical_path_stability_score", return_value=85.0
        ), patch.object(
            analytics_service, "_calculate_resource_utilization_score", return_value=75.0
        ), patch.object(
            analytics_service, "_calculate_completion_rate_score", return_value=60.0
        ):
            score = await analytics_service.calculate_project_health_score(
                mock_project.id, mock_db
            )

        # Expected: 80*0.3 + 85*0.25 + 75*0.2 + 95*0.15 + 60*0.1 = 79.5
        # (Risk score is ~95 for low spread)
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 70  # Should be healthy

    @pytest.mark.asyncio
    async def test_health_score_without_simulation(
        self, analytics_service, mock_project
    ):
        """Test health score calculation without simulation data."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock database queries
        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = mock_project

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [project_result, sim_result]

        # Mock helper methods
        with patch.object(
            analytics_service, "_calculate_schedule_adherence_score", return_value=80.0
        ), patch.object(
            analytics_service, "_calculate_critical_path_stability_score", return_value=85.0
        ), patch.object(
            analytics_service, "_calculate_resource_utilization_score", return_value=75.0
        ), patch.object(
            analytics_service, "_calculate_completion_rate_score", return_value=60.0
        ):
            score = await analytics_service.calculate_project_health_score(
                mock_project.id, mock_db
            )

        # Risk score defaults to 50 without simulation
        assert isinstance(score, float)
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_health_score_project_not_found(self, analytics_service):
        """Test health score with non-existent project."""
        mock_db = AsyncMock(spec=AsyncSession)

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = project_result

        with pytest.raises(AnalyticsError, match="Project .* not found"):
            await analytics_service.calculate_project_health_score(uuid4(), mock_db)


class TestGetCriticalPathMetrics:
    """Test get_critical_path_metrics function."""

    @pytest.mark.asyncio
    async def test_critical_path_basic(self, analytics_service, mock_project):
        """Test basic critical path calculation."""
        mock_db = AsyncMock(spec=AsyncSession)

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = mock_project
        mock_db.execute.return_value = project_result

        # Mock the stability score
        with patch.object(
            analytics_service, "_calculate_critical_path_stability_score", return_value=85.0
        ):
            metrics = await analytics_service.get_critical_path_metrics(
                mock_project.id, mock_db
            )

        assert "critical_tasks" in metrics
        assert "total_duration" in metrics
        assert "float_time" in metrics
        assert "risk_tasks" in metrics
        assert "path_stability_score" in metrics

        # Verify critical path exists
        assert isinstance(metrics["critical_tasks"], list)
        assert len(metrics["critical_tasks"]) > 0

        # Verify total duration is calculated
        assert metrics["total_duration"] > 0

        # Verify float time is calculated for all tasks
        assert isinstance(metrics["float_time"], dict)

    @pytest.mark.asyncio
    async def test_critical_path_empty_project(self, analytics_service):
        """Test critical path with empty project (no tasks)."""
        mock_db = AsyncMock(spec=AsyncSession)

        empty_project = Project(
            id=uuid4(),
            name="Empty Project",
            owner_id=uuid4(),
            configuration={"tasks": []},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = empty_project
        mock_db.execute.return_value = project_result

        metrics = await analytics_service.get_critical_path_metrics(
            empty_project.id, mock_db
        )

        assert metrics["critical_tasks"] == []
        assert metrics["total_duration"] == 0
        assert metrics["float_time"] == {}
        assert metrics["risk_tasks"] == []
        assert metrics["path_stability_score"] == 100.0

    @pytest.mark.asyncio
    async def test_critical_path_project_not_found(self, analytics_service):
        """Test critical path with non-existent project."""
        mock_db = AsyncMock(spec=AsyncSession)

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = project_result

        with pytest.raises(AnalyticsError, match="Project .* not found"):
            await analytics_service.get_critical_path_metrics(uuid4(), mock_db)


class TestGetResourceUtilization:
    """Test get_resource_utilization function."""

    @pytest.mark.asyncio
    async def test_resource_utilization_basic(self, analytics_service, mock_project):
        """Test basic resource utilization calculation."""
        mock_db = AsyncMock(spec=AsyncSession)

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = mock_project
        mock_db.execute.return_value = project_result

        metrics = await analytics_service.get_resource_utilization(
            mock_project.id, mock_db
        )

        assert "total_resources" in metrics
        assert "allocated_resources" in metrics
        assert "utilization_pct" in metrics
        assert "over_allocated" in metrics
        assert "under_utilized" in metrics
        assert "resource_timeline" in metrics

        assert metrics["total_resources"] == 3
        assert metrics["allocated_resources"] == 3
        assert isinstance(metrics["utilization_pct"], float)

    @pytest.mark.asyncio
    async def test_resource_utilization_over_allocated(self, analytics_service):
        """Test resource utilization with over-allocated resources."""
        mock_db = AsyncMock(spec=AsyncSession)

        project = Project(
            id=uuid4(),
            name="Overloaded Project",
            owner_id=uuid4(),
            configuration={
                "tasks": [
                    {"id": "T1", "duration": 50.0, "resources": ["R1"]},
                    {"id": "T2", "duration": 30.0, "resources": ["R1"]},
                ],
                "resources": {"R1": {"name": "Overloaded Resource"}},
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = project
        mock_db.execute.return_value = project_result

        metrics = await analytics_service.get_resource_utilization(project.id, mock_db)

        # Resource R1 has 80 days of work (> 40 threshold)
        assert len(metrics["over_allocated"]) == 1
        assert metrics["over_allocated"][0]["resource_id"] == "R1"
        assert metrics["over_allocated"][0]["workload_days"] == 80.0

    @pytest.mark.asyncio
    async def test_resource_utilization_under_utilized(self, analytics_service):
        """Test resource utilization with under-utilized resources."""
        mock_db = AsyncMock(spec=AsyncSession)

        project = Project(
            id=uuid4(),
            name="Light Project",
            owner_id=uuid4(),
            configuration={
                "tasks": [{"id": "T1", "duration": 5.0, "resources": ["R1"]}],
                "resources": {"R1": {"name": "Under-utilized Resource"}},
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = project
        mock_db.execute.return_value = project_result

        metrics = await analytics_service.get_resource_utilization(project.id, mock_db)

        # Resource R1 has 5 days of work (< 10 threshold)
        assert len(metrics["under_utilized"]) == 1
        assert metrics["under_utilized"][0]["resource_id"] == "R1"
        assert metrics["under_utilized"][0]["workload_days"] == 5.0


class TestGetSimulationSummary:
    """Test get_simulation_summary function."""

    @pytest.mark.asyncio
    async def test_simulation_summary_with_data(
        self, analytics_service, mock_simulation_result
    ):
        """Test simulation summary with existing simulation data."""
        mock_db = AsyncMock(spec=AsyncSession)

        mock_simulation_result.project_id = uuid4()

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = mock_simulation_result
        mock_db.execute.return_value = sim_result

        summary = await analytics_service.get_simulation_summary(
            mock_simulation_result.project_id, mock_db
        )

        assert "percentiles" in summary
        assert "mean_duration" in summary
        assert "std_deviation" in summary
        assert "risk_level" in summary
        assert "confidence_80pct_range" in summary
        assert "histogram_data" in summary

        # Verify percentiles
        assert summary["percentiles"]["p10"] == 20.5
        assert summary["percentiles"]["p50"] == 25.0
        assert summary["percentiles"]["p90"] == 30.5

        # Verify risk level (spread = (30.5-25)/25 = 22% = medium)
        assert summary["risk_level"] == "medium"

        # Verify confidence interval
        assert summary["confidence_80pct_range"] == [20.5, 30.5]

    @pytest.mark.asyncio
    async def test_simulation_summary_low_risk(self, analytics_service):
        """Test simulation summary with low risk (narrow spread)."""
        mock_db = AsyncMock(spec=AsyncSession)

        low_risk_sim = SimulationResult(
            id=1,
            project_id=uuid4(),
            user_id=uuid4(),
            iterations=1000,
            task_count=4,
            project_start_date=date.today(),
            mean_duration=25.0,
            median_duration=25.0,
            std_deviation=1.5,
            confidence_intervals={
                10: 23.0,
                50: 25.0,
                75: 26.5,
                90: 27.5,  # Only 10% spread
                95: 28.0,
            },
            created_at=datetime.now(),
        )

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = low_risk_sim
        mock_db.execute.return_value = sim_result

        summary = await analytics_service.get_simulation_summary(
            low_risk_sim.project_id, mock_db
        )

        assert summary["risk_level"] == "low"

    @pytest.mark.asyncio
    async def test_simulation_summary_high_risk(self, analytics_service):
        """Test simulation summary with high risk (wide spread)."""
        mock_db = AsyncMock(spec=AsyncSession)

        high_risk_sim = SimulationResult(
            id=1,
            project_id=uuid4(),
            user_id=uuid4(),
            iterations=1000,
            task_count=4,
            project_start_date=date.today(),
            mean_duration=30.0,
            median_duration=25.0,
            std_deviation=8.0,
            confidence_intervals={
                10: 18.0,
                50: 25.0,
                75: 32.0,
                90: 40.0,  # 60% spread
                95: 45.0,
            },
            created_at=datetime.now(),
        )

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = high_risk_sim
        mock_db.execute.return_value = sim_result

        summary = await analytics_service.get_simulation_summary(
            high_risk_sim.project_id, mock_db
        )

        assert summary["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_simulation_summary_no_data(self, analytics_service):
        """Test simulation summary with no simulation data."""
        mock_db = AsyncMock(spec=AsyncSession)

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = sim_result

        summary = await analytics_service.get_simulation_summary(uuid4(), mock_db)

        assert summary["mean_duration"] == 0.0
        assert summary["std_deviation"] == 0.0
        assert summary["risk_level"] == "unknown"
        assert summary["histogram_data"] == []


class TestGetProgressMetrics:
    """Test get_progress_metrics function."""

    @pytest.mark.asyncio
    async def test_progress_metrics_basic(self, analytics_service, mock_project):
        """Test basic progress metrics calculation."""
        mock_db = AsyncMock(spec=AsyncSession)

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = mock_project

        # Mock no baseline simulation
        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [project_result, sim_result]

        metrics = await analytics_service.get_progress_metrics(
            mock_project.id, mock_db
        )

        assert "completion_pct" in metrics
        assert "tasks_completed" in metrics
        assert "tasks_total" in metrics
        assert "on_time_pct" in metrics
        assert "delayed_tasks" in metrics
        assert "burn_rate" in metrics
        assert "estimated_completion_date" in metrics
        assert "variance_from_plan" in metrics

        # 2 completed out of 4 tasks
        assert metrics["tasks_completed"] == 2
        assert metrics["tasks_total"] == 4
        assert metrics["completion_pct"] == 50.0

    @pytest.mark.asyncio
    async def test_progress_metrics_with_delays(self, analytics_service):
        """Test progress metrics with delayed tasks."""
        mock_db = AsyncMock(spec=AsyncSession)

        project = Project(
            id=uuid4(),
            name="Delayed Project",
            owner_id=uuid4(),
            configuration={
                "tasks": [
                    {"id": "T1", "status": "completed", "is_delayed": True},
                    {"id": "T2", "status": "completed", "is_delayed": False},
                    {"id": "T3", "status": "in_progress", "is_delayed": True},
                ]
            },
            created_at=datetime.now() - timedelta(days=10),
            updated_at=datetime.now(),
        )

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = project

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [project_result, sim_result]

        metrics = await analytics_service.get_progress_metrics(project.id, mock_db)

        assert metrics["delayed_tasks"] == 2
        # 1 on-time task out of 2 completed
        assert metrics["on_time_pct"] == 50.0

    @pytest.mark.asyncio
    async def test_progress_metrics_burn_rate(self, analytics_service):
        """Test burn rate calculation."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Project is 20 days old with 10 completed tasks
        project = Project(
            id=uuid4(),
            name="Active Project",
            owner_id=uuid4(),
            configuration={
                "tasks": [{"id": f"T{i}", "status": "completed"} for i in range(10)]
                + [{"id": f"T{i}", "status": "pending"} for i in range(10, 15)]
            },
            created_at=datetime.now() - timedelta(days=20),
            updated_at=datetime.now(),
        )

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = project

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [project_result, sim_result]

        metrics = await analytics_service.get_progress_metrics(project.id, mock_db)

        # Burn rate = 10 tasks / 20 days = 0.5 tasks/day
        assert metrics["burn_rate"] == 0.5
        assert metrics["estimated_completion_date"] is not None


class TestPerformance:
    """Performance tests for analytics service."""

    @pytest.mark.asyncio
    async def test_large_project_performance(self, analytics_service):
        """Test performance with 1000 tasks (must complete in <500ms)."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Create large project with 1000 tasks
        tasks = []
        for i in range(1000):
            task = {
                "id": f"T{i}",
                "duration": 5.0,
                "dependencies": [f"T{i-1}"] if i > 0 else [],
                "resources": [f"R{i % 50}"],
                "status": "completed" if i < 500 else "pending",
            }
            tasks.append(task)

        large_project = Project(
            id=uuid4(),
            name="Large Project",
            owner_id=uuid4(),
            configuration={"tasks": tasks, "resources": {}},
            created_at=datetime.now() - timedelta(days=100),
            updated_at=datetime.now(),
        )

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = large_project

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = None

        # Mock the stability score
        with patch.object(
            analytics_service, "_calculate_critical_path_stability_score", return_value=85.0
        ):
            mock_db.execute.side_effect = [project_result, sim_result]

            start_time = time.time()
            metrics = await analytics_service.get_critical_path_metrics(
                large_project.id, mock_db
            )
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

            # Must complete in less than 500ms
            assert elapsed_time < 500, f"Critical path took {elapsed_time}ms (>500ms limit)"
            assert len(metrics["critical_tasks"]) > 0


class TestCaching:
    """Test Redis caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_hit(self, analytics_service, mock_project):
        """Test cache hit scenario."""
        mock_db = AsyncMock(spec=AsyncSession)

        cached_data = {"health_score": 85.5}

        with patch.object(
            analytics_service, "_get_cached", return_value=cached_data
        ) as mock_get:
            score = await analytics_service.calculate_project_health_score(
                mock_project.id, mock_db
            )

            mock_get.assert_called_once()
            assert score == 85.5
            # DB should not be queried
            mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_and_set(self, analytics_service, mock_project):
        """Test cache miss and subsequent cache set."""
        mock_db = AsyncMock(spec=AsyncSession)

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = mock_project

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [project_result, sim_result]

        with patch.object(
            analytics_service, "_get_cached", return_value=None
        ) as mock_get, patch.object(
            analytics_service, "_set_cached"
        ) as mock_set, patch.object(
            analytics_service, "_calculate_schedule_adherence_score", return_value=80.0
        ), patch.object(
            analytics_service, "_calculate_critical_path_stability_score", return_value=85.0
        ), patch.object(
            analytics_service, "_calculate_resource_utilization_score", return_value=75.0
        ), patch.object(
            analytics_service, "_calculate_completion_rate_score", return_value=60.0
        ):
            score = await analytics_service.calculate_project_health_score(
                mock_project.id, mock_db
            )

            mock_get.assert_called_once()
            mock_set.assert_called_once()
            assert isinstance(score, float)


class TestHelperMethods:
    """Test private helper methods."""

    def test_calculate_risk_score_low_risk(self, analytics_service):
        """Test risk score calculation for low risk simulation."""
        sim_result = SimulationResult(
            id=1,
            project_id=uuid4(),
            user_id=uuid4(),
            iterations=1000,
            task_count=4,
            project_start_date=date.today(),
            mean_duration=25.0,
            median_duration=25.0,
            std_deviation=1.5,
            confidence_intervals={50: 25.0, 90: 28.0},  # 12% spread
            created_at=datetime.now(),
        )

        score = analytics_service._calculate_risk_score(sim_result)
        assert score == 95.0

    def test_calculate_risk_score_medium_risk(self, analytics_service):
        """Test risk score calculation for medium risk simulation."""
        sim_result = SimulationResult(
            id=1,
            project_id=uuid4(),
            user_id=uuid4(),
            iterations=1000,
            task_count=4,
            project_start_date=date.today(),
            mean_duration=27.0,
            median_duration=25.0,
            std_deviation=3.0,
            confidence_intervals={50: 25.0, 90: 30.0},  # 20% spread
            created_at=datetime.now(),
        )

        score = analytics_service._calculate_risk_score(sim_result)
        assert score == 75.0

    def test_calculate_risk_score_high_risk(self, analytics_service):
        """Test risk score calculation for high risk simulation."""
        sim_result = SimulationResult(
            id=1,
            project_id=uuid4(),
            user_id=uuid4(),
            iterations=1000,
            task_count=4,
            project_start_date=date.today(),
            mean_duration=30.0,
            median_duration=25.0,
            std_deviation=6.0,
            confidence_intervals={50: 25.0, 90: 40.0},  # 60% spread
            created_at=datetime.now(),
        )

        score = analytics_service._calculate_risk_score(sim_result)
        assert score == 50.0

    @pytest.mark.asyncio
    async def test_calculate_resource_utilization_score_optimal(
        self, analytics_service, mock_project
    ):
        """Test resource utilization score with optimal utilization."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Create project with 80% utilization (optimal)
        project = Project(
            id=uuid4(),
            name="Well-Balanced Project",
            owner_id=uuid4(),
            configuration={
                "tasks": [
                    {"id": "T1", "duration": 16.0, "resources": ["R1"]},
                    {"id": "T2", "duration": 16.0, "resources": ["R2"]},
                    {"id": "T3", "duration": 16.0, "resources": ["R3"]},
                ],
                "resources": {"R1": {}, "R2": {}, "R3": {}},
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Mock get_resource_utilization to return 80%
        with patch.object(
            analytics_service,
            "get_resource_utilization",
            return_value={"utilization_pct": 80.0},
        ):
            score = await analytics_service._calculate_resource_utilization_score(
                project, mock_db
            )
            assert score == 100.0

    @pytest.mark.asyncio
    async def test_calculate_resource_utilization_score_under_utilized(
        self, analytics_service, mock_project
    ):
        """Test resource utilization score with under-utilization."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock get_resource_utilization to return 50%
        with patch.object(
            analytics_service,
            "get_resource_utilization",
            return_value={"utilization_pct": 50.0},
        ):
            score = await analytics_service._calculate_resource_utilization_score(
                mock_project, mock_db
            )
            # 50/70*100 = 71.4
            assert 70 <= score <= 72

    @pytest.mark.asyncio
    async def test_calculate_resource_utilization_score_over_utilized(
        self, analytics_service, mock_project
    ):
        """Test resource utilization score with over-utilization."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock get_resource_utilization to return 110%
        with patch.object(
            analytics_service,
            "get_resource_utilization",
            return_value={"utilization_pct": 110.0},
        ):
            score = await analytics_service._calculate_resource_utilization_score(
                mock_project, mock_db
            )
            # 200 - 110 = 90
            assert score == 90.0

    @pytest.mark.asyncio
    async def test_close_redis_connection(self, analytics_service):
        """Test closing Redis connection."""
        mock_redis = AsyncMock()
        analytics_service._redis_client = mock_redis

        await analytics_service.close()

        mock_redis.close.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_progress_metrics_zero_age_project(self, analytics_service):
        """Test progress metrics with brand new project (zero age)."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Project created now (zero age)
        project = Project(
            id=uuid4(),
            name="Brand New Project",
            owner_id=uuid4(),
            configuration={
                "tasks": [
                    {"id": "T1", "status": "pending"},
                    {"id": "T2", "status": "pending"},
                ]
            },
            created_at=datetime.now(),  # Just created
            updated_at=datetime.now(),
        )

        project_result = MagicMock()
        project_result.scalar_one_or_none.return_value = project

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [project_result, sim_result]

        metrics = await analytics_service.get_progress_metrics(project.id, mock_db)

        # Burn rate should be 0 for brand new project
        assert metrics["burn_rate"] == 0.0
        assert metrics["estimated_completion_date"] is None

    @pytest.mark.asyncio
    async def test_simulation_summary_zero_p50(self, analytics_service):
        """Test simulation summary with zero P50 (edge case)."""
        mock_db = AsyncMock(spec=AsyncSession)

        edge_case_sim = SimulationResult(
            id=1,
            project_id=uuid4(),
            user_id=uuid4(),
            iterations=100,
            task_count=1,
            project_start_date=date.today(),
            mean_duration=0.0,
            median_duration=0.0,
            std_deviation=0.0,
            confidence_intervals={10: 0.0, 50: 0.0, 90: 0.0, 95: 0.0},
            created_at=datetime.now(),
        )

        sim_result = MagicMock()
        sim_result.scalar_one_or_none.return_value = edge_case_sim
        mock_db.execute.return_value = sim_result

        summary = await analytics_service.get_simulation_summary(
            edge_case_sim.project_id, mock_db
        )

        # Should handle zero P50 gracefully
        assert summary["risk_level"] == "unknown"
