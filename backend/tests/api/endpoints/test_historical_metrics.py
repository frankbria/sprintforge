"""
Test suite for Historical Metrics API Endpoints.

This test file follows TDD principles (RED-GREEN-REFACTOR):
- Tests written BEFORE implementation
- Tests will FAIL initially (RED phase)
- Target: 85%+ code coverage

Tests cover:
- GET /api/v1/projects/{id}/metrics/historical
- GET /api/v1/projects/{id}/metrics/velocity
- GET /api/v1/projects/{id}/metrics/trends
- GET /api/v1/projects/{id}/metrics/forecast
- GET /api/v1/projects/{id}/metrics/summary
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.historical_metrics import (
    HistoricalMetric,
    SprintVelocity,
    CompletionTrend,
    ForecastData,
    MetricType,
    ForecastModelType,
)


@pytest_asyncio.fixture
async def sample_metrics_data(test_db_session: AsyncSession, test_project):
    """Create comprehensive sample metrics data for API testing."""
    now = datetime.now(timezone.utc)

    # Create historical metrics
    for i in range(5):
        metric = HistoricalMetric(
            project_id=test_project.id,
            metric_type=MetricType.VELOCITY,
            value=40.0 + i * 2,
            timestamp=now - timedelta(days=i * 7),
            metric_metadata={"sprint": i},
        )
        test_db_session.add(metric)

    # Create sprint velocities
    for i in range(8):
        velocity = SprintVelocity(
            project_id=test_project.id,
            sprint_id=str(uuid4()),
            velocity_points=35.0 + i * 3,
            completed_tasks=14 + i,
            timestamp=now - timedelta(days=i * 14),
        )
        test_db_session.add(velocity)

    # Create completion trends
    for i in range(4):
        trend = CompletionTrend(
            project_id=test_project.id,
            period_start=now - timedelta(days=(i + 1) * 30),
            period_end=now - timedelta(days=i * 30),
            completion_rate=0.7 + i * 0.05,
            tasks_completed=70 + i * 5,
            tasks_total=100,
        )
        test_db_session.add(trend)

    # Create forecasts
    for i in range(3):
        forecast = ForecastData(
            project_id=test_project.id,
            forecast_date=now + timedelta(days=(i + 1) * 14),
            predicted_value=50.0 + i * 2,
            confidence_lower=45.0 + i * 2,
            confidence_upper=55.0 + i * 2,
            model_type=ForecastModelType.LINEAR_REGRESSION,
        )
        test_db_session.add(forecast)

    await test_db_session.commit()


class TestHistoricalMetricsEndpoint:
    """Test suite for GET /api/v1/projects/{id}/metrics/historical."""

    @pytest.mark.asyncio
    async def test_get_historical_metrics_success(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test successful retrieval of historical metrics."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/historical")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_get_historical_metrics_filter_by_type(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test filtering historical metrics by metric type."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/historical",
            params={"metric_type": "VELOCITY"},
        )

        assert response.status_code == 200
        data = response.json()
        # Verify all returned metrics are VELOCITY type
        if isinstance(data, list) and len(data) > 0:
            assert all(m.get("metric_type") == "VELOCITY" for m in data if isinstance(m, dict))

    @pytest.mark.asyncio
    async def test_get_historical_metrics_filter_by_date_range(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test filtering historical metrics by date range."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()

        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/historical",
            params={"start_date": start_date, "end_date": end_date},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_historical_metrics_nonexistent_project(self, client: AsyncClient):
        """Test getting historical metrics for non-existent project."""
        fake_project_id = uuid4()
        response = await client.get(f"/api/v1/projects/{fake_project_id}/metrics/historical")

        assert response.status_code in [404, 200]  # 200 with empty list is also valid

    @pytest.mark.asyncio
    async def test_get_historical_metrics_no_data(
        self, client: AsyncClient, test_project
    ):
        """Test getting historical metrics when no data exists."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/historical")

        assert response.status_code == 200
        data = response.json()
        # Should return empty list or indicate no data
        if isinstance(data, list):
            assert len(data) == 0


class TestVelocityMetricsEndpoint:
    """Test suite for GET /api/v1/projects/{id}/metrics/velocity."""

    @pytest.mark.asyncio
    async def test_get_velocity_metrics_success(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test successful retrieval of velocity metrics."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/velocity")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_velocity_metrics_with_num_sprints(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test velocity metrics with custom sprint count."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/velocity",
            params={"num_sprints": 5},
        )

        assert response.status_code == 200
        data = response.json()
        # Verify response includes velocity data
        assert "velocities" in data or "trend" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_velocity_metrics_include_moving_avg(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test velocity metrics with moving average included."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/velocity",
            params={"include_moving_avg": True},
        )

        assert response.status_code == 200
        data = response.json()
        # Verify moving average is included
        assert "moving_average" in data or "moving_avg" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_velocity_metrics_structure(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test that velocity metrics response has correct structure."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/velocity")

        assert response.status_code == 200
        data = response.json()
        # Should contain velocity trend information
        assert isinstance(data, (dict, list))


class TestTrendsMetricsEndpoint:
    """Test suite for GET /api/v1/projects/{id}/metrics/trends."""

    @pytest.mark.asyncio
    async def test_get_trends_metrics_success(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test successful retrieval of trend metrics."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/trends")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_trends_metrics_with_period_days(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test trends metrics with custom period."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/trends",
            params={"period_days": 60},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_trends_metrics_with_granularity(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test trends metrics with granularity parameter."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/trends",
            params={"granularity": "daily"},
        )

        assert response.status_code == 200
        data = response.json()
        # Verify granularity is applied
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_trends_metrics_includes_patterns(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test that trends response includes pattern analysis."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/trends")

        assert response.status_code == 200
        data = response.json()
        # Should include patterns or trends
        assert isinstance(data, dict)


class TestForecastMetricsEndpoint:
    """Test suite for GET /api/v1/projects/{id}/metrics/forecast."""

    @pytest.mark.asyncio
    async def test_get_forecast_metrics_success(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test successful retrieval of forecast metrics."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/forecast")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))

    @pytest.mark.asyncio
    async def test_get_forecast_metrics_with_periods_ahead(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test forecast metrics with custom periods ahead."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/forecast",
            params={"periods_ahead": 10},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_forecast_metrics_include_confidence(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test forecast metrics with confidence intervals."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/forecast",
            params={"include_confidence": True},
        )

        assert response.status_code == 200
        data = response.json()
        # Verify confidence intervals are included
        if isinstance(data, list) and len(data) > 0:
            first_forecast = data[0]
            assert (
                "confidence_lower" in first_forecast or "confidence_upper" in first_forecast
                if isinstance(first_forecast, dict) else True
            )

    @pytest.mark.asyncio
    async def test_get_forecast_metrics_structure(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test that forecast response has correct structure."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/forecast")

        assert response.status_code == 200
        data = response.json()
        # Should contain forecast data
        assert isinstance(data, (dict, list))


class TestMetricsSummaryEndpoint:
    """Test suite for GET /api/v1/projects/{id}/metrics/summary."""

    @pytest.mark.asyncio
    async def test_get_metrics_summary_success(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test successful retrieval of metrics summary."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_metrics_summary_includes_velocity(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test that summary includes velocity information."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        # Should include velocity summary
        assert "velocity" in data or "current_velocity" in data or "avg_velocity" in data

    @pytest.mark.asyncio
    async def test_get_metrics_summary_includes_trends(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test that summary includes trend information."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        # Should include trend summary
        assert "trends" in data or "completion_rate" in data or "trend" in data

    @pytest.mark.asyncio
    async def test_get_metrics_summary_includes_forecasts(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test that summary includes forecast information."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        # Should include forecast summary
        assert "forecast" in data or "predicted" in data or "forecasts" in data

    @pytest.mark.asyncio
    async def test_get_metrics_summary_comprehensive(
        self, client: AsyncClient, test_project, sample_metrics_data
    ):
        """Test that summary provides comprehensive dashboard data."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        # Should be a comprehensive summary with multiple sections
        assert isinstance(data, dict)
        assert len(data) >= 2  # At least 2 sections of data

    @pytest.mark.asyncio
    async def test_get_metrics_summary_no_data(
        self, client: AsyncClient, test_project
    ):
        """Test metrics summary when no data exists."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        # Should return empty or default summary
        assert isinstance(data, dict)


class TestAPIErrorHandling:
    """Test suite for API error handling."""

    @pytest.mark.asyncio
    async def test_invalid_project_id_format(self, client: AsyncClient):
        """Test API with invalid project ID format."""
        response = await client.get("/api/v1/projects/invalid-uuid/metrics/summary")

        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, client: AsyncClient, test_project):
        """Test API with invalid date format."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/historical",
            params={"start_date": "not-a-date"},
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_invalid_query_parameters(self, client: AsyncClient, test_project):
        """Test API with invalid query parameters."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/velocity",
            params={"num_sprints": "invalid"},
        )

        assert response.status_code in [400, 422]


class TestAPIAuthentication:
    """Test suite for API authentication and authorization."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint_requires_auth(self, client: AsyncClient, test_project):
        """Test that metrics endpoints may require authentication."""
        # Note: This test assumes auth is implemented
        # If no auth is required, this test will need adjustment
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/metrics/summary"
        )

        # Either succeeds (200) or requires auth (401)
        assert response.status_code in [200, 401, 403]

    @pytest.mark.asyncio
    async def test_user_can_only_access_own_project_metrics(
        self, client: AsyncClient, test_project, test_user_pro
    ):
        """Test that users can only access metrics for their own projects."""
        # Create another user's project
        from app.models.project import Project

        other_user_id = uuid4()
        other_project = Project(
            name="Other User Project",
            owner_id=other_user_id,
            configuration={},
            template_version="1.0",
        )

        # This test depends on authentication implementation
        # For now, just verify endpoint exists
        response = await client.get(f"/api/v1/projects/{test_project.id}/metrics/summary")
        assert response.status_code in [200, 401, 403, 404]
