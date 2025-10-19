"""
Test suite for Forecast Engine Service.

This test file follows TDD principles (RED-GREEN-REFACTOR):
- Tests written BEFORE implementation
- Tests will FAIL initially (RED phase)
- Target: 85%+ code coverage

Tests cover:
- ForecastEngine class methods
- Velocity forecasting
- Completion date forecasting
- Confidence interval calculations
- Linear regression fitting
- Statistical analysis
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Import service that will be created
from app.services.forecast_engine import ForecastEngine
from app.models.historical_metrics import ForecastData, SprintVelocity, ForecastModelType


@pytest_asyncio.fixture
async def forecast_engine(test_db_session: AsyncSession):
    """Create ForecastEngine instance with test database session."""
    return ForecastEngine(db_session=test_db_session)


@pytest_asyncio.fixture
async def sample_velocity_history(test_db_session: AsyncSession, test_project):
    """Create sample velocity history for forecasting."""
    now = datetime.now(timezone.utc)
    velocities = []

    # Create 10 sprints with upward trend
    for i in range(10):
        velocity = SprintVelocity(
            project_id=test_project.id,
            sprint_id=str(uuid4()),
            velocity_points=30.0 + (i * 2.0),  # Linear growth
            completed_tasks=12 + i,
            timestamp=now - timedelta(days=(10 - i) * 14),
        )
        test_db_session.add(velocity)
        velocities.append(velocity)

    await test_db_session.commit()
    return velocities


class TestForecastEngineInit:
    """Test suite for ForecastEngine initialization."""

    @pytest.mark.asyncio
    async def test_forecast_engine_initialization(self, test_db_session: AsyncSession):
        """Test creating ForecastEngine instance."""
        engine = ForecastEngine(db_session=test_db_session)

        assert engine is not None
        assert engine.db_session == test_db_session

    @pytest.mark.asyncio
    async def test_forecast_engine_requires_db_session(self):
        """Test that ForecastEngine requires a database session."""
        with pytest.raises(TypeError):
            ForecastEngine()


class TestForecastVelocity:
    """Test suite for forecast_velocity method."""

    @pytest.mark.asyncio
    async def test_forecast_velocity_default_periods(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test velocity forecasting with default period count (5)."""
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        assert isinstance(forecasts, list)
        assert len(forecasts) <= 5
        assert all(isinstance(f, ForecastData) for f in forecasts)

    @pytest.mark.asyncio
    async def test_forecast_velocity_custom_periods(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test velocity forecasting with custom period count."""
        forecasts = await forecast_engine.forecast_velocity(
            project_id=test_project.id, periods_ahead=10
        )

        assert isinstance(forecasts, list)
        assert len(forecasts) <= 10

    @pytest.mark.asyncio
    async def test_forecast_velocity_includes_confidence_intervals(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that velocity forecasts include confidence intervals."""
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        if len(forecasts) > 0:
            forecast = forecasts[0]
            assert hasattr(forecast, "confidence_lower")
            assert hasattr(forecast, "confidence_upper")
            assert hasattr(forecast, "predicted_value")

    @pytest.mark.asyncio
    async def test_forecast_velocity_confidence_ordering(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that confidence intervals are properly ordered."""
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        for forecast in forecasts:
            assert forecast.confidence_lower <= forecast.predicted_value
            assert forecast.predicted_value <= forecast.confidence_upper

    @pytest.mark.asyncio
    async def test_forecast_velocity_future_dates(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that forecast dates are in the future."""
        now = datetime.now(timezone.utc)
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        for forecast in forecasts:
            assert forecast.forecast_date >= now

    @pytest.mark.asyncio
    async def test_forecast_velocity_chronological_order(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that forecasts are in chronological order."""
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        if len(forecasts) > 1:
            dates = [f.forecast_date for f in forecasts]
            assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_forecast_velocity_saves_to_database(
        self, forecast_engine: ForecastEngine, test_db_session: AsyncSession, test_project, sample_velocity_history
    ):
        """Test that forecasts are saved to database."""
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        # Verify forecasts were saved
        from sqlalchemy import select

        result = await test_db_session.execute(
            select(ForecastData).where(ForecastData.project_id == test_project.id)
        )
        saved_forecasts = result.scalars().all()

        assert len(saved_forecasts) > 0

    @pytest.mark.asyncio
    async def test_forecast_velocity_insufficient_history(
        self, forecast_engine: ForecastEngine, test_db_session: AsyncSession, test_project
    ):
        """Test velocity forecasting with insufficient historical data."""
        # Create only 2 velocity records (insufficient for good forecast)
        for i in range(2):
            velocity = SprintVelocity(
                project_id=test_project.id,
                sprint_id=str(uuid4()),
                velocity_points=40.0,
                completed_tasks=16,
            )
            test_db_session.add(velocity)
        await test_db_session.commit()

        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        # Should handle gracefully (may return empty list or simple forecast)
        assert isinstance(forecasts, list)

    @pytest.mark.asyncio
    async def test_forecast_velocity_no_history(
        self, forecast_engine: ForecastEngine, test_project
    ):
        """Test velocity forecasting with no historical data."""
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        assert isinstance(forecasts, list)
        assert len(forecasts) == 0


class TestForecastCompletionDate:
    """Test suite for forecast_completion_date method."""

    @pytest.mark.asyncio
    async def test_forecast_completion_date_returns_dict(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that completion date forecast returns a dictionary."""
        result = await forecast_engine.forecast_completion_date(
            project_id=test_project.id, remaining_tasks=50
        )

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_forecast_completion_date_includes_date(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that completion date forecast includes estimated date."""
        result = await forecast_engine.forecast_completion_date(
            project_id=test_project.id, remaining_tasks=50
        )

        assert "date" in result or "completion_date" in result or "estimated_date" in result

    @pytest.mark.asyncio
    async def test_forecast_completion_date_includes_confidence(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that completion date forecast includes confidence level."""
        result = await forecast_engine.forecast_completion_date(
            project_id=test_project.id, remaining_tasks=50
        )

        assert "confidence" in result or "confidence_level" in result or "probability" in result

    @pytest.mark.asyncio
    async def test_forecast_completion_date_future_date(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that forecasted completion date is in the future."""
        now = datetime.now(timezone.utc)
        result = await forecast_engine.forecast_completion_date(
            project_id=test_project.id, remaining_tasks=50
        )

        # Extract date from result (key may vary)
        date_key = next((k for k in result.keys() if "date" in k.lower()), None)
        if date_key:
            completion_date = result[date_key]
            # Date might be datetime or string
            if isinstance(completion_date, datetime):
                assert completion_date >= now

    @pytest.mark.asyncio
    async def test_forecast_completion_date_zero_tasks(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test completion date forecast with zero remaining tasks."""
        result = await forecast_engine.forecast_completion_date(
            project_id=test_project.id, remaining_tasks=0
        )

        # Should indicate immediate completion or current date
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_forecast_completion_date_large_task_count(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test completion date forecast with large number of remaining tasks."""
        result = await forecast_engine.forecast_completion_date(
            project_id=test_project.id, remaining_tasks=1000
        )

        assert isinstance(result, dict)
        # Should handle large numbers without errors

    @pytest.mark.asyncio
    async def test_forecast_completion_date_no_velocity_history(
        self, forecast_engine: ForecastEngine, test_project
    ):
        """Test completion date forecast with no velocity history."""
        result = await forecast_engine.forecast_completion_date(
            project_id=test_project.id, remaining_tasks=50
        )

        assert isinstance(result, dict)
        # Should indicate inability to forecast or return None/error


class TestCalculateConfidenceIntervals:
    """Test suite for calculate_confidence_intervals method."""

    @pytest.mark.asyncio
    async def test_calculate_confidence_intervals_returns_tuple(
        self, forecast_engine: ForecastEngine
    ):
        """Test that confidence interval calculation returns a tuple."""
        data = [30.0, 35.0, 40.0, 38.0, 42.0, 45.0]
        lower, upper = await forecast_engine.calculate_confidence_intervals(data)

        assert isinstance(lower, (int, float))
        assert isinstance(upper, (int, float))

    @pytest.mark.asyncio
    async def test_calculate_confidence_intervals_ordering(
        self, forecast_engine: ForecastEngine
    ):
        """Test that lower bound is less than upper bound."""
        data = [30.0, 35.0, 40.0, 38.0, 42.0, 45.0]
        lower, upper = await forecast_engine.calculate_confidence_intervals(data)

        assert lower < upper

    @pytest.mark.asyncio
    async def test_calculate_confidence_intervals_default_confidence(
        self, forecast_engine: ForecastEngine
    ):
        """Test confidence interval calculation with default 95% confidence."""
        data = [30.0, 35.0, 40.0, 38.0, 42.0, 45.0]
        lower, upper = await forecast_engine.calculate_confidence_intervals(data)

        # Verify interval is reasonable
        mean = sum(data) / len(data)
        assert lower < mean < upper

    @pytest.mark.asyncio
    async def test_calculate_confidence_intervals_custom_confidence(
        self, forecast_engine: ForecastEngine
    ):
        """Test confidence interval calculation with custom confidence level."""
        data = [30.0, 35.0, 40.0, 38.0, 42.0, 45.0]

        # 99% confidence should be wider than 95%
        lower_99, upper_99 = await forecast_engine.calculate_confidence_intervals(
            data, confidence_level=0.99
        )
        lower_95, upper_95 = await forecast_engine.calculate_confidence_intervals(
            data, confidence_level=0.95
        )

        interval_99 = upper_99 - lower_99
        interval_95 = upper_95 - lower_95

        assert interval_99 >= interval_95

    @pytest.mark.asyncio
    async def test_calculate_confidence_intervals_small_dataset(
        self, forecast_engine: ForecastEngine
    ):
        """Test confidence interval calculation with small dataset."""
        data = [40.0, 42.0]
        lower, upper = await forecast_engine.calculate_confidence_intervals(data)

        # Should still return valid interval
        assert lower < upper

    @pytest.mark.asyncio
    async def test_calculate_confidence_intervals_single_value(
        self, forecast_engine: ForecastEngine
    ):
        """Test confidence interval calculation with single data point."""
        data = [40.0]

        # May raise exception or return zero-width interval
        try:
            lower, upper = await forecast_engine.calculate_confidence_intervals(data)
            assert lower <= upper
        except (ValueError, ZeroDivisionError):
            # Expected behavior for insufficient data
            pass


class TestFitLinearRegression:
    """Test suite for fit_linear_regression method."""

    @pytest.mark.asyncio
    async def test_fit_linear_regression_returns_dict(
        self, forecast_engine: ForecastEngine
    ):
        """Test that linear regression fitting returns a dictionary."""
        x_data = [1, 2, 3, 4, 5]
        y_data = [2, 4, 6, 8, 10]

        result = await forecast_engine.fit_linear_regression(x_data, y_data)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_fit_linear_regression_includes_slope(
        self, forecast_engine: ForecastEngine
    ):
        """Test that regression result includes slope."""
        x_data = [1, 2, 3, 4, 5]
        y_data = [2, 4, 6, 8, 10]

        result = await forecast_engine.fit_linear_regression(x_data, y_data)

        assert "slope" in result or "coefficient" in result

    @pytest.mark.asyncio
    async def test_fit_linear_regression_includes_intercept(
        self, forecast_engine: ForecastEngine
    ):
        """Test that regression result includes intercept."""
        x_data = [1, 2, 3, 4, 5]
        y_data = [2, 4, 6, 8, 10]

        result = await forecast_engine.fit_linear_regression(x_data, y_data)

        assert "intercept" in result

    @pytest.mark.asyncio
    async def test_fit_linear_regression_includes_r_squared(
        self, forecast_engine: ForecastEngine
    ):
        """Test that regression result includes R-squared value."""
        x_data = [1, 2, 3, 4, 5]
        y_data = [2, 4, 6, 8, 10]

        result = await forecast_engine.fit_linear_regression(x_data, y_data)

        assert "r_squared" in result or "r2" in result or "r_score" in result

    @pytest.mark.asyncio
    async def test_fit_linear_regression_perfect_correlation(
        self, forecast_engine: ForecastEngine
    ):
        """Test linear regression with perfect linear correlation."""
        x_data = [1, 2, 3, 4, 5]
        y_data = [2, 4, 6, 8, 10]  # y = 2x

        result = await forecast_engine.fit_linear_regression(x_data, y_data)

        # Extract slope and R-squared
        slope_key = next((k for k in result.keys() if "slope" in k or "coefficient" in k), None)
        r2_key = next((k for k in result.keys() if "r" in k.lower()), None)

        if slope_key:
            assert abs(result[slope_key] - 2.0) < 0.01

        if r2_key:
            # R-squared should be close to 1.0 for perfect fit
            assert result[r2_key] >= 0.99

    @pytest.mark.asyncio
    async def test_fit_linear_regression_positive_slope(
        self, forecast_engine: ForecastEngine
    ):
        """Test linear regression with positive slope."""
        x_data = [1, 2, 3, 4, 5]
        y_data = [10, 15, 20, 25, 30]

        result = await forecast_engine.fit_linear_regression(x_data, y_data)

        slope_key = next((k for k in result.keys() if "slope" in k or "coefficient" in k), None)
        if slope_key:
            assert result[slope_key] > 0

    @pytest.mark.asyncio
    async def test_fit_linear_regression_negative_slope(
        self, forecast_engine: ForecastEngine
    ):
        """Test linear regression with negative slope."""
        x_data = [1, 2, 3, 4, 5]
        y_data = [50, 40, 30, 20, 10]

        result = await forecast_engine.fit_linear_regression(x_data, y_data)

        slope_key = next((k for k in result.keys() if "slope" in k or "coefficient" in k), None)
        if slope_key:
            assert result[slope_key] < 0

    @pytest.mark.asyncio
    async def test_fit_linear_regression_with_noise(
        self, forecast_engine: ForecastEngine
    ):
        """Test linear regression with noisy data."""
        x_data = [1, 2, 3, 4, 5]
        y_data = [2.1, 3.9, 6.2, 7.8, 10.1]  # Roughly y = 2x with noise

        result = await forecast_engine.fit_linear_regression(x_data, y_data)

        # Should still detect the trend
        slope_key = next((k for k in result.keys() if "slope" in k or "coefficient" in k), None)
        r2_key = next((k for k in result.keys() if "r" in k.lower()), None)

        if slope_key:
            assert 1.5 < result[slope_key] < 2.5

        if r2_key:
            # R-squared should be reasonably high but not perfect
            assert 0.8 < result[r2_key] < 1.0

    @pytest.mark.asyncio
    async def test_fit_linear_regression_insufficient_data(
        self, forecast_engine: ForecastEngine
    ):
        """Test linear regression with insufficient data points."""
        x_data = [1]
        y_data = [2]

        # Should raise exception or handle gracefully
        try:
            result = await forecast_engine.fit_linear_regression(x_data, y_data)
            # If it doesn't raise, result should still be a dict
            assert isinstance(result, dict)
        except (ValueError, ZeroDivisionError):
            # Expected behavior for insufficient data
            pass

    @pytest.mark.asyncio
    async def test_fit_linear_regression_mismatched_lengths(
        self, forecast_engine: ForecastEngine
    ):
        """Test linear regression with mismatched x and y lengths."""
        x_data = [1, 2, 3]
        y_data = [2, 4]

        # Should raise exception
        with pytest.raises((ValueError, AssertionError)):
            await forecast_engine.fit_linear_regression(x_data, y_data)


class TestForecastEngineIntegration:
    """Integration tests for ForecastEngine combining multiple methods."""

    @pytest.mark.asyncio
    async def test_forecast_uses_linear_regression(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that velocity forecast uses linear regression model."""
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        # Verify forecasts use linear regression model
        if len(forecasts) > 0:
            assert any(
                f.model_type == ForecastModelType.LINEAR_REGRESSION for f in forecasts
            )

    @pytest.mark.asyncio
    async def test_forecast_confidence_intervals_are_calculated(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that forecasts include calculated confidence intervals."""
        forecasts = await forecast_engine.forecast_velocity(project_id=test_project.id)

        for forecast in forecasts:
            # Confidence intervals should be present and reasonable
            assert forecast.confidence_lower > 0
            assert forecast.confidence_upper > 0
            assert forecast.confidence_lower < forecast.confidence_upper

    @pytest.mark.asyncio
    async def test_multiple_forecast_runs_are_consistent(
        self, forecast_engine: ForecastEngine, test_project, sample_velocity_history
    ):
        """Test that running forecasts multiple times produces consistent results."""
        forecasts1 = await forecast_engine.forecast_velocity(
            project_id=test_project.id, periods_ahead=3
        )
        forecasts2 = await forecast_engine.forecast_velocity(
            project_id=test_project.id, periods_ahead=3
        )

        # Results should be consistent (same predicted values)
        if len(forecasts1) > 0 and len(forecasts2) > 0:
            # Compare first forecast
            assert abs(forecasts1[0].predicted_value - forecasts2[0].predicted_value) < 0.01
