"""
Test suite for Historical Metrics models.

This test file follows TDD principles (RED-GREEN-REFACTOR):
- Tests written BEFORE implementation
- Tests will FAIL initially (RED phase)
- Target: 85%+ code coverage

Tests cover:
- HistoricalMetric model
- SprintVelocity model
- CompletionTrend model
- ForecastData model
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import models that will be created
from app.models.historical_metrics import (
    HistoricalMetric,
    SprintVelocity,
    CompletionTrend,
    ForecastData,
    MetricType,
    ForecastModelType,
)


@pytest_asyncio.fixture
async def test_sprint(test_db_session: AsyncSession, test_project):
    """Create a test sprint for velocity tracking."""
    # Note: This assumes Sprint model exists - if not, we'll create mock data
    # For now, returning a mock sprint_id
    return str(uuid4())


class TestHistoricalMetricModel:
    """Test suite for HistoricalMetric model."""

    @pytest.mark.asyncio
    async def test_create_historical_metric(self, test_db_session: AsyncSession, test_project):
        """Test creating a basic historical metric record."""
        metric = HistoricalMetric(
            project_id=test_project.id,
            metric_type=MetricType.VELOCITY,
            value=42.5,
            timestamp=datetime.now(timezone.utc),
            metric_metadata={"source": "test"},
        )

        test_db_session.add(metric)
        await test_db_session.commit()
        await test_db_session.refresh(metric)

        assert metric.id is not None
        assert metric.project_id == test_project.id
        assert metric.metric_type == MetricType.VELOCITY
        assert metric.value == 42.5
        assert metric.metric_metadata == {"source": "test"}

    @pytest.mark.asyncio
    async def test_historical_metric_timestamp_defaults_to_now(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test that timestamp defaults to current time if not provided."""
        before_creation = datetime.now(timezone.utc)

        metric = HistoricalMetric(
            project_id=test_project.id,
            metric_type=MetricType.COMPLETION_RATE,
            value=0.85,
        )

        test_db_session.add(metric)
        await test_db_session.commit()
        await test_db_session.refresh(metric)

        after_creation = datetime.now(timezone.utc)

        # Allow for small time differences (SQLite truncates microseconds)
        assert metric.timestamp is not None
        assert metric.timestamp.tzinfo == timezone.utc
        # Check that timestamp is within reasonable range (before - 1 second to after + 1 second)
        assert (before_creation - timedelta(seconds=1)) <= metric.timestamp <= (after_creation + timedelta(seconds=1))

    @pytest.mark.asyncio
    async def test_historical_metric_metadata_defaults_to_empty_dict(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test that metadata defaults to empty dict."""
        metric = HistoricalMetric(
            project_id=test_project.id,
            metric_type=MetricType.VELOCITY,
            value=10.0,
        )

        test_db_session.add(metric)
        await test_db_session.commit()
        await test_db_session.refresh(metric)

        assert metric.metric_metadata == {}

    @pytest.mark.asyncio
    async def test_historical_metric_with_complex_metadata(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test storing complex nested JSON in metadata field."""
        complex_metadata = {
            "calculation_method": "monte_carlo",
            "iterations": 10000,
            "confidence_level": 0.95,
            "parameters": {
                "min": 1,
                "max": 100,
                "mean": 50,
            },
        }

        metric = HistoricalMetric(
            project_id=test_project.id,
            metric_type=MetricType.FORECAST,
            value=75.0,
            metric_metadata=complex_metadata,
        )

        test_db_session.add(metric)
        await test_db_session.commit()
        await test_db_session.refresh(metric)

        assert metric.metric_metadata == complex_metadata
        assert metric.metric_metadata["parameters"]["mean"] == 50

    @pytest.mark.asyncio
    async def test_query_metrics_by_type(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test querying metrics filtered by metric_type."""
        # Create multiple metrics of different types
        metrics = [
            HistoricalMetric(
                project_id=test_project.id,
                metric_type=MetricType.VELOCITY,
                value=10.0,
            ),
            HistoricalMetric(
                project_id=test_project.id,
                metric_type=MetricType.VELOCITY,
                value=12.0,
            ),
            HistoricalMetric(
                project_id=test_project.id,
                metric_type=MetricType.COMPLETION_RATE,
                value=0.75,
            ),
        ]

        for metric in metrics:
            test_db_session.add(metric)
        await test_db_session.commit()

        # Query only velocity metrics
        result = await test_db_session.execute(
            select(HistoricalMetric).where(
                HistoricalMetric.project_id == test_project.id,
                HistoricalMetric.metric_type == MetricType.VELOCITY,
            )
        )
        velocity_metrics = result.scalars().all()

        assert len(velocity_metrics) == 2
        assert all(m.metric_type == MetricType.VELOCITY for m in velocity_metrics)

    @pytest.mark.asyncio
    async def test_query_metrics_by_time_range(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test querying metrics within a specific time range."""
        now = datetime.now(timezone.utc)

        # Create metrics at different times
        metrics = [
            HistoricalMetric(
                project_id=test_project.id,
                metric_type=MetricType.VELOCITY,
                value=10.0,
                timestamp=now - timedelta(days=10),
            ),
            HistoricalMetric(
                project_id=test_project.id,
                metric_type=MetricType.VELOCITY,
                value=12.0,
                timestamp=now - timedelta(days=5),
            ),
            HistoricalMetric(
                project_id=test_project.id,
                metric_type=MetricType.VELOCITY,
                value=15.0,
                timestamp=now - timedelta(days=1),
            ),
        ]

        for metric in metrics:
            test_db_session.add(metric)
        await test_db_session.commit()

        # Query metrics from last 7 days
        start_date = now - timedelta(days=7)
        result = await test_db_session.execute(
            select(HistoricalMetric).where(
                HistoricalMetric.project_id == test_project.id,
                HistoricalMetric.timestamp >= start_date,
            )
        )
        recent_metrics = result.scalars().all()

        assert len(recent_metrics) == 2
        assert all(m.timestamp >= start_date for m in recent_metrics)


class TestSprintVelocityModel:
    """Test suite for SprintVelocity model."""

    @pytest.mark.asyncio
    async def test_create_sprint_velocity(
        self, test_db_session: AsyncSession, test_project, test_sprint
    ):
        """Test creating a sprint velocity record."""
        velocity = SprintVelocity(
            project_id=test_project.id,
            sprint_id=test_sprint,
            velocity_points=42.5,
            completed_tasks=15,
            timestamp=datetime.now(timezone.utc),
        )

        test_db_session.add(velocity)
        await test_db_session.commit()
        await test_db_session.refresh(velocity)

        assert velocity.id is not None
        assert velocity.project_id == test_project.id
        assert velocity.sprint_id == test_sprint
        assert velocity.velocity_points == 42.5
        assert velocity.completed_tasks == 15

    @pytest.mark.asyncio
    async def test_sprint_velocity_timestamp_defaults(
        self, test_db_session: AsyncSession, test_project, test_sprint
    ):
        """Test that timestamp defaults to current time."""
        before = datetime.now(timezone.utc)

        velocity = SprintVelocity(
            project_id=test_project.id,
            sprint_id=test_sprint,
            velocity_points=30.0,
            completed_tasks=10,
        )

        test_db_session.add(velocity)
        await test_db_session.commit()
        await test_db_session.refresh(velocity)

        after = datetime.now(timezone.utc)

        # Allow for small time differences (SQLite truncates microseconds)
        assert velocity.timestamp is not None
        assert velocity.timestamp.tzinfo == timezone.utc
        # Check that timestamp is within reasonable range (before - 1 second to after + 1 second)
        assert (before - timedelta(seconds=1)) <= velocity.timestamp <= (after + timedelta(seconds=1))

    @pytest.mark.asyncio
    async def test_query_velocities_by_project(
        self, test_db_session: AsyncSession, test_project, test_user_pro
    ):
        """Test querying all velocities for a project."""
        # Create another project for comparison
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

        # Create velocities for both projects
        velocities = [
            SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=10.0,
                completed_tasks=5,
            ),
            SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=12.0,
                completed_tasks=6,
            ),
            SprintVelocity(
                project_id=other_project.id,
                sprint_id=str(uuid4()),
                velocity_points=20.0,
                completed_tasks=8,
            ),
        ]

        for velocity in velocities:
            test_db_session.add(velocity)
        await test_db_session.commit()

        # Query velocities for test_project only
        result = await test_db_session.execute(
            select(SprintVelocity).where(
                SprintVelocity.project_id == test_project.id
            )
        )
        project_velocities = result.scalars().all()

        assert len(project_velocities) == 2
        assert all(v.project_id == test_project.id for v in project_velocities)

    @pytest.mark.asyncio
    async def test_sprint_velocity_zero_values(
        self, test_db_session: AsyncSession, test_project, test_sprint
    ):
        """Test that sprint velocity can handle zero values."""
        velocity = SprintVelocity(
            project_id=test_project.id,
            sprint_id=test_sprint,
            velocity_points=0.0,
            completed_tasks=0,
        )

        test_db_session.add(velocity)
        await test_db_session.commit()
        await test_db_session.refresh(velocity)

        assert velocity.velocity_points == 0.0
        assert velocity.completed_tasks == 0


class TestCompletionTrendModel:
    """Test suite for CompletionTrend model."""

    @pytest.mark.asyncio
    async def test_create_completion_trend(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test creating a completion trend record."""
        now = datetime.now(timezone.utc)

        trend = CompletionTrend(
            project_id=test_project.id,
            period_start=now - timedelta(days=30),
            period_end=now,
            completion_rate=0.85,
            tasks_completed=85,
            tasks_total=100,
        )

        test_db_session.add(trend)
        await test_db_session.commit()
        await test_db_session.refresh(trend)

        assert trend.id is not None
        assert trend.project_id == test_project.id
        assert trend.completion_rate == 0.85
        assert trend.tasks_completed == 85
        assert trend.tasks_total == 100

    @pytest.mark.asyncio
    async def test_completion_trend_with_100_percent_rate(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test completion trend with 100% completion rate."""
        now = datetime.now(timezone.utc)

        trend = CompletionTrend(
            project_id=test_project.id,
            period_start=now - timedelta(days=7),
            period_end=now,
            completion_rate=1.0,
            tasks_completed=50,
            tasks_total=50,
        )

        test_db_session.add(trend)
        await test_db_session.commit()
        await test_db_session.refresh(trend)

        assert trend.completion_rate == 1.0
        assert trend.tasks_completed == trend.tasks_total

    @pytest.mark.asyncio
    async def test_completion_trend_with_zero_rate(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test completion trend with 0% completion rate."""
        now = datetime.now(timezone.utc)

        trend = CompletionTrend(
            project_id=test_project.id,
            period_start=now - timedelta(days=7),
            period_end=now,
            completion_rate=0.0,
            tasks_completed=0,
            tasks_total=100,
        )

        test_db_session.add(trend)
        await test_db_session.commit()
        await test_db_session.refresh(trend)

        assert trend.completion_rate == 0.0
        assert trend.tasks_completed == 0

    @pytest.mark.asyncio
    async def test_query_trends_by_period(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test querying trends for overlapping periods."""
        now = datetime.now(timezone.utc)

        # Create trends for different periods
        trends = [
            CompletionTrend(
                project_id=test_project.id,
                period_start=now - timedelta(days=30),
                period_end=now - timedelta(days=15),
                completion_rate=0.7,
                tasks_completed=70,
                tasks_total=100,
            ),
            CompletionTrend(
                project_id=test_project.id,
                period_start=now - timedelta(days=14),
                period_end=now,
                completion_rate=0.9,
                tasks_completed=90,
                tasks_total=100,
            ),
        ]

        for trend in trends:
            test_db_session.add(trend)
        await test_db_session.commit()

        # Query trends that end after a certain date
        cutoff_date = now - timedelta(days=20)
        result = await test_db_session.execute(
            select(CompletionTrend).where(
                CompletionTrend.project_id == test_project.id,
                CompletionTrend.period_end >= cutoff_date,
            )
        )
        recent_trends = result.scalars().all()

        # Both trends end after cutoff: now-15 >= now-20 and now >= now-20
        assert len(recent_trends) == 2


class TestForecastDataModel:
    """Test suite for ForecastData model."""

    @pytest.mark.asyncio
    async def test_create_forecast_data(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test creating a forecast data record."""
        forecast = ForecastData(
            project_id=test_project.id,
            forecast_date=datetime.now(timezone.utc) + timedelta(days=30),
            predicted_value=45.5,
            confidence_lower=40.0,
            confidence_upper=51.0,
            model_type=ForecastModelType.LINEAR_REGRESSION,
        )

        test_db_session.add(forecast)
        await test_db_session.commit()
        await test_db_session.refresh(forecast)

        assert forecast.id is not None
        assert forecast.project_id == test_project.id
        assert forecast.predicted_value == 45.5
        assert forecast.confidence_lower == 40.0
        assert forecast.confidence_upper == 51.0
        assert forecast.model_type == ForecastModelType.LINEAR_REGRESSION

    @pytest.mark.asyncio
    async def test_forecast_data_with_moving_average_model(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test forecast using moving average model type."""
        forecast = ForecastData(
            project_id=test_project.id,
            forecast_date=datetime.now(timezone.utc) + timedelta(days=14),
            predicted_value=38.0,
            confidence_lower=35.0,
            confidence_upper=41.0,
            model_type=ForecastModelType.MOVING_AVERAGE,
        )

        test_db_session.add(forecast)
        await test_db_session.commit()
        await test_db_session.refresh(forecast)

        assert forecast.model_type == ForecastModelType.MOVING_AVERAGE

    @pytest.mark.asyncio
    async def test_forecast_confidence_intervals_ordering(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test that confidence intervals are properly ordered."""
        forecast = ForecastData(
            project_id=test_project.id,
            forecast_date=datetime.now(timezone.utc) + timedelta(days=7),
            predicted_value=50.0,
            confidence_lower=45.0,
            confidence_upper=55.0,
            model_type=ForecastModelType.LINEAR_REGRESSION,
        )

        test_db_session.add(forecast)
        await test_db_session.commit()
        await test_db_session.refresh(forecast)

        # Verify ordering: lower < predicted < upper
        assert forecast.confidence_lower < forecast.predicted_value
        assert forecast.predicted_value < forecast.confidence_upper

    @pytest.mark.asyncio
    async def test_query_forecasts_by_date_range(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test querying forecasts for a specific date range."""
        now = datetime.now(timezone.utc)

        # Create forecasts for different future dates
        forecasts = [
            ForecastData(
                project_id=test_project.id,
                forecast_date=now + timedelta(days=7),
                predicted_value=40.0,
                confidence_lower=35.0,
                confidence_upper=45.0,
                model_type=ForecastModelType.LINEAR_REGRESSION,
            ),
            ForecastData(
                project_id=test_project.id,
                forecast_date=now + timedelta(days=14),
                predicted_value=45.0,
                confidence_lower=40.0,
                confidence_upper=50.0,
                model_type=ForecastModelType.LINEAR_REGRESSION,
            ),
            ForecastData(
                project_id=test_project.id,
                forecast_date=now + timedelta(days=30),
                predicted_value=55.0,
                confidence_lower=48.0,
                confidence_upper=62.0,
                model_type=ForecastModelType.LINEAR_REGRESSION,
            ),
        ]

        for forecast in forecasts:
            test_db_session.add(forecast)
        await test_db_session.commit()

        # Query forecasts for next 2 weeks
        end_date = now + timedelta(days=15)
        result = await test_db_session.execute(
            select(ForecastData).where(
                ForecastData.project_id == test_project.id,
                ForecastData.forecast_date <= end_date,
            )
        )
        near_term_forecasts = result.scalars().all()

        assert len(near_term_forecasts) == 2

    @pytest.mark.asyncio
    async def test_forecast_with_narrow_confidence_interval(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test forecast with very narrow confidence interval (high confidence)."""
        forecast = ForecastData(
            project_id=test_project.id,
            forecast_date=datetime.now(timezone.utc) + timedelta(days=3),
            predicted_value=50.0,
            confidence_lower=49.5,
            confidence_upper=50.5,
            model_type=ForecastModelType.MOVING_AVERAGE,
        )

        test_db_session.add(forecast)
        await test_db_session.commit()
        await test_db_session.refresh(forecast)

        confidence_range = forecast.confidence_upper - forecast.confidence_lower
        assert confidence_range == 1.0  # Narrow range indicates high confidence

    @pytest.mark.asyncio
    async def test_forecast_with_wide_confidence_interval(
        self, test_db_session: AsyncSession, test_project
    ):
        """Test forecast with wide confidence interval (low confidence)."""
        forecast = ForecastData(
            project_id=test_project.id,
            forecast_date=datetime.now(timezone.utc) + timedelta(days=60),
            predicted_value=70.0,
            confidence_lower=50.0,
            confidence_upper=90.0,
            model_type=ForecastModelType.LINEAR_REGRESSION,
        )

        test_db_session.add(forecast)
        await test_db_session.commit()
        await test_db_session.refresh(forecast)

        confidence_range = forecast.confidence_upper - forecast.confidence_lower
        assert confidence_range == 40.0  # Wide range indicates low confidence


class TestMetricTypeEnum:
    """Test suite for MetricType enum."""

    def test_metric_type_values(self):
        """Test that all expected metric types are defined."""
        assert hasattr(MetricType, "VELOCITY")
        assert hasattr(MetricType, "COMPLETION_RATE")
        assert hasattr(MetricType, "FORECAST")
        assert hasattr(MetricType, "BURNDOWN")


class TestForecastModelTypeEnum:
    """Test suite for ForecastModelType enum."""

    def test_forecast_model_type_values(self):
        """Test that all expected forecast model types are defined."""
        assert hasattr(ForecastModelType, "LINEAR_REGRESSION")
        assert hasattr(ForecastModelType, "MOVING_AVERAGE")
        assert hasattr(ForecastModelType, "EXPONENTIAL_SMOOTHING")
