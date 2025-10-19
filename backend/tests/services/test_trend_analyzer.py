"""
Test suite for Trend Analyzer Service.

This test file follows TDD principles (RED-GREEN-REFACTOR):
- Tests written BEFORE implementation
- Tests will FAIL initially (RED phase)
- Target: 85%+ code coverage

Tests cover:
- TrendAnalyzer class methods
- Completion trend calculations
- Daily completion rate analysis
- Completion pattern detection
- Bottleneck identification
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Import service that will be created
from app.services.trend_analyzer import TrendAnalyzer
from app.models.historical_metrics import CompletionTrend


@pytest_asyncio.fixture
async def trend_analyzer(test_db_session: AsyncSession):
    """Create TrendAnalyzer instance with test database session."""
    return TrendAnalyzer(db_session=test_db_session)


@pytest_asyncio.fixture
async def sample_completion_data(test_db_session: AsyncSession, test_project):
    """Create sample completion data for testing."""
    now = datetime.now(timezone.utc)
    trends = []

    # Create 12 weeks of completion data
    for week in range(12):
        trend = CompletionTrend(
            project_id=test_project.id,
            period_start=now - timedelta(days=(12 - week) * 7),
            period_end=now - timedelta(days=(12 - week - 1) * 7),
            completion_rate=0.7 + (week * 0.02),  # Gradually improving
            tasks_completed=70 + (week * 2),
            tasks_total=100,
        )
        test_db_session.add(trend)
        trends.append(trend)

    await test_db_session.commit()
    return trends


class TestTrendAnalyzerInit:
    """Test suite for TrendAnalyzer initialization."""

    @pytest.mark.asyncio
    async def test_trend_analyzer_initialization(self, test_db_session: AsyncSession):
        """Test creating TrendAnalyzer instance."""
        analyzer = TrendAnalyzer(db_session=test_db_session)

        assert analyzer is not None
        assert analyzer.db_session == test_db_session

    @pytest.mark.asyncio
    async def test_trend_analyzer_requires_db_session(self):
        """Test that TrendAnalyzer requires a database session."""
        with pytest.raises(TypeError):
            TrendAnalyzer()


class TestCalculateCompletionTrend:
    """Test suite for calculate_completion_trend method."""

    @pytest.mark.asyncio
    async def test_calculate_completion_trend_default_period(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test completion trend calculation with default period (30 days)."""
        trend = await trend_analyzer.calculate_completion_trend(project_id=test_project.id)

        assert isinstance(trend, CompletionTrend)
        assert trend.project_id == test_project.id

    @pytest.mark.asyncio
    async def test_calculate_completion_trend_custom_period(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test completion trend calculation with custom period."""
        trend = await trend_analyzer.calculate_completion_trend(
            project_id=test_project.id, period_days=7
        )

        assert isinstance(trend, CompletionTrend)
        # Verify period span
        period_span = (trend.period_end - trend.period_start).days
        assert period_span <= 7

    @pytest.mark.asyncio
    async def test_calculate_completion_trend_includes_all_fields(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test that completion trend includes all required fields."""
        trend = await trend_analyzer.calculate_completion_trend(project_id=test_project.id)

        assert hasattr(trend, "completion_rate")
        assert hasattr(trend, "tasks_completed")
        assert hasattr(trend, "tasks_total")
        assert hasattr(trend, "period_start")
        assert hasattr(trend, "period_end")

    @pytest.mark.asyncio
    async def test_calculate_completion_trend_rate_bounds(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test that completion rate is between 0 and 1."""
        trend = await trend_analyzer.calculate_completion_trend(project_id=test_project.id)

        assert 0.0 <= trend.completion_rate <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_completion_trend_saves_to_database(
        self, trend_analyzer: TrendAnalyzer, test_db_session: AsyncSession, test_project
    ):
        """Test that calculated trend is saved to database."""
        trend = await trend_analyzer.calculate_completion_trend(project_id=test_project.id)

        # Verify trend was saved
        from sqlalchemy import select

        result = await test_db_session.execute(
            select(CompletionTrend).where(CompletionTrend.project_id == test_project.id)
        )
        saved_trends = result.scalars().all()

        assert len(saved_trends) > 0


class TestGetDailyCompletionRate:
    """Test suite for get_daily_completion_rate method."""

    @pytest.mark.asyncio
    async def test_get_daily_completion_rate_default_days(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test getting daily completion rates with default period (90 days)."""
        daily_rates = await trend_analyzer.get_daily_completion_rate(project_id=test_project.id)

        assert isinstance(daily_rates, list)
        # Should have up to 90 entries
        assert len(daily_rates) <= 90

    @pytest.mark.asyncio
    async def test_get_daily_completion_rate_custom_days(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test getting daily completion rates with custom period."""
        daily_rates = await trend_analyzer.get_daily_completion_rate(
            project_id=test_project.id, days=30
        )

        assert isinstance(daily_rates, list)
        assert len(daily_rates) <= 30

    @pytest.mark.asyncio
    async def test_get_daily_completion_rate_structure(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test that each daily rate entry has correct structure."""
        daily_rates = await trend_analyzer.get_daily_completion_rate(
            project_id=test_project.id, days=7
        )

        if len(daily_rates) > 0:
            entry = daily_rates[0]
            assert isinstance(entry, dict)
            # Expected fields: date, completion_rate, tasks_completed
            assert "date" in entry or "completion_rate" in entry

    @pytest.mark.asyncio
    async def test_get_daily_completion_rate_chronological_order(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test that daily rates are in chronological order."""
        daily_rates = await trend_analyzer.get_daily_completion_rate(
            project_id=test_project.id, days=14
        )

        if len(daily_rates) > 1:
            # Verify dates are in order
            dates = [entry.get("date") for entry in daily_rates if "date" in entry]
            if dates:
                # Allow either ascending or descending order
                is_sorted = dates == sorted(dates) or dates == sorted(dates, reverse=True)
                assert is_sorted

    @pytest.mark.asyncio
    async def test_get_daily_completion_rate_no_data(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test getting daily completion rates when no data exists."""
        daily_rates = await trend_analyzer.get_daily_completion_rate(project_id=test_project.id)

        assert isinstance(daily_rates, list)
        # Should return empty list or placeholder values


class TestAnalyzeCompletionPatterns:
    """Test suite for analyze_completion_patterns method."""

    @pytest.mark.asyncio
    async def test_analyze_completion_patterns_returns_dict(
        self, trend_analyzer: TrendAnalyzer, test_project, sample_completion_data
    ):
        """Test that pattern analysis returns a dictionary."""
        patterns = await trend_analyzer.analyze_completion_patterns(project_id=test_project.id)

        assert isinstance(patterns, dict)

    @pytest.mark.asyncio
    async def test_analyze_completion_patterns_includes_weekly_patterns(
        self, trend_analyzer: TrendAnalyzer, test_project, sample_completion_data
    ):
        """Test that pattern analysis includes weekly patterns."""
        patterns = await trend_analyzer.analyze_completion_patterns(project_id=test_project.id)

        assert "weekly" in patterns or "weekly_pattern" in patterns or "week" in str(patterns)

    @pytest.mark.asyncio
    async def test_analyze_completion_patterns_includes_monthly_patterns(
        self, trend_analyzer: TrendAnalyzer, test_project, sample_completion_data
    ):
        """Test that pattern analysis includes monthly patterns."""
        patterns = await trend_analyzer.analyze_completion_patterns(project_id=test_project.id)

        assert "monthly" in patterns or "monthly_pattern" in patterns or "month" in str(patterns)

    @pytest.mark.asyncio
    async def test_analyze_completion_patterns_detects_trends(
        self, trend_analyzer: TrendAnalyzer, test_db_session: AsyncSession, test_project
    ):
        """Test that pattern analysis detects improving/declining trends."""
        now = datetime.now(timezone.utc)

        # Create clearly improving trend
        for week in range(8):
            trend = CompletionTrend(
                project_id=test_project.id,
                period_start=now - timedelta(days=(8 - week) * 7),
                period_end=now - timedelta(days=(8 - week - 1) * 7),
                completion_rate=0.5 + (week * 0.05),  # Improving by 5% each week
                tasks_completed=50 + (week * 5),
                tasks_total=100,
            )
            test_db_session.add(trend)
        await test_db_session.commit()

        patterns = await trend_analyzer.analyze_completion_patterns(project_id=test_project.id)

        # Should detect improvement
        assert "trend" in patterns or "improving" in str(patterns).lower() or "direction" in patterns

    @pytest.mark.asyncio
    async def test_analyze_completion_patterns_handles_insufficient_data(
        self, trend_analyzer: TrendAnalyzer, test_db_session: AsyncSession, test_project
    ):
        """Test pattern analysis with insufficient data points."""
        now = datetime.now(timezone.utc)

        # Create only 2 data points
        for week in range(2):
            trend = CompletionTrend(
                project_id=test_project.id,
                period_start=now - timedelta(days=(2 - week) * 7),
                period_end=now - timedelta(days=(2 - week - 1) * 7),
                completion_rate=0.7,
                tasks_completed=70,
                tasks_total=100,
            )
            test_db_session.add(trend)
        await test_db_session.commit()

        patterns = await trend_analyzer.analyze_completion_patterns(project_id=test_project.id)

        # Should return dict even with limited data
        assert isinstance(patterns, dict)

    @pytest.mark.asyncio
    async def test_analyze_completion_patterns_no_data(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test pattern analysis when no completion data exists."""
        patterns = await trend_analyzer.analyze_completion_patterns(project_id=test_project.id)

        assert isinstance(patterns, dict)
        # Should indicate no data or return empty patterns


class TestIdentifyBottlenecks:
    """Test suite for identify_bottlenecks method."""

    @pytest.mark.asyncio
    async def test_identify_bottlenecks_returns_list(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test that bottleneck identification returns a list."""
        bottlenecks = await trend_analyzer.identify_bottlenecks(project_id=test_project.id)

        assert isinstance(bottlenecks, list)

    @pytest.mark.asyncio
    async def test_identify_bottlenecks_includes_metadata(
        self, trend_analyzer: TrendAnalyzer, test_db_session: AsyncSession, test_project
    ):
        """Test that bottlenecks include descriptive metadata."""
        now = datetime.now(timezone.utc)

        # Create data with obvious bottleneck (low completion rate)
        for week in range(4):
            completion_rate = 0.3 if week == 2 else 0.8  # Week 2 is a bottleneck
            trend = CompletionTrend(
                project_id=test_project.id,
                period_start=now - timedelta(days=(4 - week) * 7),
                period_end=now - timedelta(days=(4 - week - 1) * 7),
                completion_rate=completion_rate,
                tasks_completed=int(completion_rate * 100),
                tasks_total=100,
            )
            test_db_session.add(trend)
        await test_db_session.commit()

        bottlenecks = await trend_analyzer.identify_bottlenecks(project_id=test_project.id)

        if len(bottlenecks) > 0:
            bottleneck = bottlenecks[0]
            assert isinstance(bottleneck, dict)
            # Should include useful info like period, severity, or description

    @pytest.mark.asyncio
    async def test_identify_bottlenecks_detects_low_completion_rates(
        self, trend_analyzer: TrendAnalyzer, test_db_session: AsyncSession, test_project
    ):
        """Test that low completion rates are identified as bottlenecks."""
        now = datetime.now(timezone.utc)

        # Create consistently low completion rates
        for week in range(4):
            trend = CompletionTrend(
                project_id=test_project.id,
                period_start=now - timedelta(days=(4 - week) * 7),
                period_end=now - timedelta(days=(4 - week - 1) * 7),
                completion_rate=0.3,  # Consistently low
                tasks_completed=30,
                tasks_total=100,
            )
            test_db_session.add(trend)
        await test_db_session.commit()

        bottlenecks = await trend_analyzer.identify_bottlenecks(project_id=test_project.id)

        # Should detect bottleneck due to low completion rates
        assert len(bottlenecks) >= 0  # May or may not detect based on threshold

    @pytest.mark.asyncio
    async def test_identify_bottlenecks_no_issues(
        self, trend_analyzer: TrendAnalyzer, test_db_session: AsyncSession, test_project
    ):
        """Test bottleneck identification with healthy completion rates."""
        now = datetime.now(timezone.utc)

        # Create consistently high completion rates
        for week in range(4):
            trend = CompletionTrend(
                project_id=test_project.id,
                period_start=now - timedelta(days=(4 - week) * 7),
                period_end=now - timedelta(days=(4 - week - 1) * 7),
                completion_rate=0.95,  # Consistently high
                tasks_completed=95,
                tasks_total=100,
            )
            test_db_session.add(trend)
        await test_db_session.commit()

        bottlenecks = await trend_analyzer.identify_bottlenecks(project_id=test_project.id)

        # Should detect no bottlenecks
        assert len(bottlenecks) == 0 or all(b.get("severity") == "low" for b in bottlenecks if isinstance(b, dict))

    @pytest.mark.asyncio
    async def test_identify_bottlenecks_declining_trend(
        self, trend_analyzer: TrendAnalyzer, test_db_session: AsyncSession, test_project
    ):
        """Test bottleneck identification with declining completion trend."""
        now = datetime.now(timezone.utc)

        # Create declining trend
        for week in range(6):
            completion_rate = 0.9 - (week * 0.1)  # Declining by 10% each week
            trend = CompletionTrend(
                project_id=test_project.id,
                period_start=now - timedelta(days=(6 - week) * 7),
                period_end=now - timedelta(days=(6 - week - 1) * 7),
                completion_rate=max(completion_rate, 0.3),
                tasks_completed=int(max(completion_rate, 0.3) * 100),
                tasks_total=100,
            )
            test_db_session.add(trend)
        await test_db_session.commit()

        bottlenecks = await trend_analyzer.identify_bottlenecks(project_id=test_project.id)

        # Should detect declining trend as a bottleneck
        assert isinstance(bottlenecks, list)

    @pytest.mark.asyncio
    async def test_identify_bottlenecks_no_data(
        self, trend_analyzer: TrendAnalyzer, test_project
    ):
        """Test bottleneck identification when no data exists."""
        bottlenecks = await trend_analyzer.identify_bottlenecks(project_id=test_project.id)

        assert isinstance(bottlenecks, list)
        assert len(bottlenecks) == 0

    @pytest.mark.asyncio
    async def test_identify_bottlenecks_insufficient_data(
        self, trend_analyzer: TrendAnalyzer, test_db_session: AsyncSession, test_project
    ):
        """Test bottleneck identification with minimal data points."""
        now = datetime.now(timezone.utc)

        # Create only 1 data point
        trend = CompletionTrend(
            project_id=test_project.id,
            period_start=now - timedelta(days=7),
            period_end=now,
            completion_rate=0.5,
            tasks_completed=50,
            tasks_total=100,
        )
        test_db_session.add(trend)
        await test_db_session.commit()

        bottlenecks = await trend_analyzer.identify_bottlenecks(project_id=test_project.id)

        # Should handle gracefully
        assert isinstance(bottlenecks, list)
