"""
Comprehensive tests for progress tracking and velocity formulas.

This test suite validates:
- Burndown and burnup chart calculations
- Velocity tracking and trend analysis
- Sprint capacity and commitment calculations
- Cycle time and throughput metrics
- Forecast calculations and probability
- Extension hooks for predictive analytics

All formulas are tested for mathematical soundness and real-world applicability.
"""

import pytest
from app.excel.components.templates.formula_loader import FormulaTemplateLoader


@pytest.fixture
def formula_templates():
    """Load progress formula templates for testing."""
    loader = FormulaTemplateLoader()
    loader.load_template("progress")
    return loader


class TestPercentComplete:
    """Test percent complete calculation formulas."""

    def test_percent_complete_duration_half(self, formula_templates):
        """Test percent complete based on duration at 50%."""
        formula = formula_templates.apply_template(
            "percent_complete_duration",
            actual_duration="20",
            duration="40"
        )
        # MIN(100, (20/40) * 100) = MIN(100, 50) = 50%
        assert formula == "=IF(40=0, 0, MIN(100, (20 / 40) * 100))"

    def test_percent_complete_duration_zero(self, formula_templates):
        """Test percent complete with zero duration (milestone)."""
        formula = formula_templates.apply_template(
            "percent_complete_duration",
            actual_duration="0",
            duration="0"
        )
        # Returns 0 for milestones (zero duration)
        assert "IF(0=0, 0" in formula

    def test_percent_complete_duration_over_100(self, formula_templates):
        """Test percent complete caps at 100% even if over time."""
        formula = formula_templates.apply_template(
            "percent_complete_duration",
            actual_duration="50",
            duration="40"
        )
        # MIN(100, 125) = 100% (capped)
        assert "MIN(100" in formula

    def test_percent_complete_work_based(self, formula_templates):
        """Test percent complete based on work units."""
        formula = formula_templates.apply_template(
            "percent_complete_work",
            work_completed="30",
            total_work="100"
        )
        # (30/100) * 100 = 30%
        assert formula == "=IF(100=0, 0, MIN(100, (30 / 100) * 100))"


class TestBurndownChart:
    """Test burndown chart calculation formulas."""

    def test_burndown_remaining_start(self, formula_templates):
        """Test burndown remaining work at sprint start."""
        formula = formula_templates.apply_template(
            "burndown_remaining",
            total_work="100",
            date_column="$A$2:$A$20",
            current_date="2025-01-01",
            work_completed_column="$B$2:$B$20"
        )
        # total_work - SUMIF(completed work up to date)
        assert 'SUMIF($A$2:$A$20, "<="&2025-01-01, $B$2:$B$20)' in formula
        assert "100 -" in formula

    def test_burndown_remaining_mid_sprint(self, formula_templates):
        """Test burndown remaining work mid-sprint."""
        formula = formula_templates.apply_template(
            "burndown_remaining",
            total_work="100",
            date_column="A:A",
            current_date="TODAY()",
            work_completed_column="B:B"
        )
        # Dynamic calculation using TODAY()
        assert "TODAY()" in formula

    def test_burndown_ideal_line(self, formula_templates):
        """Test ideal burndown line calculation."""
        formula = formula_templates.apply_template(
            "burndown_ideal",
            total_work="100",
            total_days="10",
            days_elapsed="5"
        )
        # 100 - ((100/10) * 5) = 100 - 50 = 50 remaining
        assert formula == "=100 - ((100 / 10) * 5)"

    def test_burndown_ideal_day_zero(self, formula_templates):
        """Test ideal burndown at sprint start (day 0)."""
        formula = formula_templates.apply_template(
            "burndown_ideal",
            total_work="80",
            total_days="8",
            days_elapsed="0"
        )
        # 80 - ((80/8) * 0) = 80 (all work remaining)
        assert formula == "=80 - ((80 / 8) * 0)"

    def test_burndown_ideal_last_day(self, formula_templates):
        """Test ideal burndown at sprint end."""
        formula = formula_templates.apply_template(
            "burndown_ideal",
            total_work="80",
            total_days="8",
            days_elapsed="8"
        )
        # 80 - ((80/8) * 8) = 0 (all work complete)
        assert formula == "=80 - ((80 / 8) * 8)"


class TestBurnupChart:
    """Test burnup chart calculation formulas."""

    def test_burnup_completed_cumulative(self, formula_templates):
        """Test burnup cumulative completed work."""
        formula = formula_templates.apply_template(
            "burnup_completed",
            date_column="$A$2:$A$20",
            current_date="2025-01-15",
            work_completed_column="$B$2:$B$20"
        )
        # SUMIF all work completed up to current date
        assert formula == '=SUMIF($A$2:$A$20, "<="&2025-01-15, $B$2:$B$20)'

    def test_burnup_ideal_line(self, formula_templates):
        """Test ideal burnup line calculation."""
        formula = formula_templates.apply_template(
            "burnup_ideal",
            total_work="100",
            total_days="10",
            days_elapsed="3"
        )
        # (100/10) * 3 = 30 work units
        assert formula == "=(100 / 10) * 3"

    def test_burnup_ideal_linear_growth(self, formula_templates):
        """Test burnup ideal shows linear growth."""
        # Day 0: (100/10) * 0 = 0
        day0 = formula_templates.apply_template(
            "burnup_ideal",
            total_work="100",
            total_days="10",
            days_elapsed="0"
        )
        # Day 10: (100/10) * 10 = 100
        day10 = formula_templates.apply_template(
            "burnup_ideal",
            total_work="100",
            total_days="10",
            days_elapsed="10"
        )
        assert "(100 / 10) * 0" in day0
        assert "(100 / 10) * 10" in day10


class TestVelocityCalculations:
    """Test velocity tracking and forecasting formulas."""

    def test_velocity_average(self, formula_templates):
        """Test average velocity calculation."""
        formula = formula_templates.apply_template(
            "velocity_average",
            sprint_velocity_range="$B$2:$B$10"
        )
        # AVERAGE of velocity across sprints
        assert formula == "=AVERAGE($B$2:$B$10)"

    def test_velocity_trend_increasing(self, formula_templates):
        """Test velocity trend with improving team performance."""
        formula = formula_templates.apply_template(
            "velocity_trend",
            sprint_velocity_range="$B$2:$B$10",
            sprint_number_range="$A$2:$A$10"
        )
        # SLOPE returns positive for improving velocity
        assert formula == "=SLOPE($B$2:$B$10, $A$2:$A$10)"

    def test_velocity_trend_stable(self, formula_templates):
        """Test velocity trend with stable team performance."""
        formula = formula_templates.apply_template(
            "velocity_trend",
            sprint_velocity_range="B:B",
            sprint_number_range="A:A"
        )
        # SLOPE near 0 indicates stable velocity
        assert "SLOPE" in formula

    def test_velocity_forecast_future_sprint(self, formula_templates):
        """Test velocity forecast for future sprint."""
        formula = formula_templates.apply_template(
            "velocity_forecast",
            future_sprint="15",
            sprint_velocity_range="$B$2:$B$10",
            sprint_number_range="$A$2:$A$10"
        )
        # FORECAST uses linear regression
        assert formula == "=FORECAST(15, $B$2:$B$10, $A$2:$A$10)"

    def test_velocity_forecast_near_term(self, formula_templates):
        """Test velocity forecast for next sprint."""
        formula = formula_templates.apply_template(
            "velocity_forecast",
            future_sprint="11",
            sprint_velocity_range="$B$2:$B$10",
            sprint_number_range="$A$2:$A$10"
        )
        # Forecast sprint 11 based on sprints 2-10
        assert "11" in formula


class TestSprintCapacity:
    """Test sprint capacity calculation formulas."""

    def test_sprint_capacity_full_team(self, formula_templates):
        """Test sprint capacity with full team and typical focus factor."""
        formula = formula_templates.apply_template(
            "sprint_capacity",
            team_size="5",
            days_per_sprint="10",
            hours_per_day="8",
            focus_factor="0.7"
        )
        # 5 * 10 * 8 * 0.7 = 280 hours
        assert formula == "=5 * 10 * 8 * 0.7"

    def test_sprint_capacity_small_team(self, formula_templates):
        """Test sprint capacity with small team."""
        formula = formula_templates.apply_template(
            "sprint_capacity",
            team_size="2",
            days_per_sprint="10",
            hours_per_day="8",
            focus_factor="0.8"
        )
        # 2 * 10 * 8 * 0.8 = 128 hours
        assert formula == "=2 * 10 * 8 * 0.8"

    def test_sprint_capacity_high_focus(self, formula_templates):
        """Test sprint capacity with high focus factor (experienced team)."""
        formula = formula_templates.apply_template(
            "sprint_capacity",
            team_size="8",
            days_per_sprint="10",
            hours_per_day="6",
            focus_factor="0.85"
        )
        # 8 * 10 * 6 * 0.85 = 408 hours
        assert formula == "=8 * 10 * 6 * 0.85"

    def test_sprint_capacity_low_focus(self, formula_templates):
        """Test sprint capacity with low focus factor (new team/distractions)."""
        formula = formula_templates.apply_template(
            "sprint_capacity",
            team_size="5",
            days_per_sprint="10",
            hours_per_day="8",
            focus_factor="0.6"
        )
        # 5 * 10 * 8 * 0.6 = 240 hours
        assert "0.6" in formula


class TestCommitmentRatio:
    """Test sprint commitment ratio calculations."""

    def test_commitment_ratio_100_percent(self, formula_templates):
        """Test commitment ratio when team delivers exactly what was committed."""
        formula = formula_templates.apply_template(
            "sprint_commitment_ratio",
            actual_completed="50",
            sprint_commitment="50"
        )
        # (50/50) * 100 = 100%
        assert formula == "=(50 / 50) * 100"

    def test_commitment_ratio_over_committed(self, formula_templates):
        """Test commitment ratio when team delivers more than committed."""
        formula = formula_templates.apply_template(
            "sprint_commitment_ratio",
            actual_completed="60",
            sprint_commitment="50"
        )
        # (60/50) * 100 = 120%
        assert formula == "=(60 / 50) * 100"

    def test_commitment_ratio_under_committed(self, formula_templates):
        """Test commitment ratio when team delivers less than committed."""
        formula = formula_templates.apply_template(
            "sprint_commitment_ratio",
            actual_completed="40",
            sprint_commitment="50"
        )
        # (40/50) * 100 = 80%
        assert formula == "=(40 / 50) * 100"


class TestWorkingDaysCalculations:
    """Test working days and date forecast calculations."""

    def test_days_remaining_with_holidays(self, formula_templates):
        """Test working days remaining calculation with holidays."""
        formula = formula_templates.apply_template(
            "days_remaining",
            current_date="2025-01-15",
            end_date="2025-01-31",
            holidays="$H$2:$H$10"
        )
        # NETWORKDAYS excludes weekends and holidays
        assert formula == "=NETWORKDAYS(2025-01-15, 2025-01-31, $H$2:$H$10)"

    def test_days_remaining_no_holidays(self, formula_templates):
        """Test working days remaining without holidays."""
        formula = formula_templates.apply_template(
            "days_remaining",
            current_date="TODAY()",
            end_date="2025-12-31",
            holidays=""
        )
        # NETWORKDAYS with empty holiday range
        assert "NETWORKDAYS(TODAY(), 2025-12-31" in formula

    def test_completion_forecast_date(self, formula_templates):
        """Test completion date forecast based on velocity."""
        formula = formula_templates.apply_template(
            "completion_forecast_date",
            current_date="2025-01-15",
            remaining_work="50",
            velocity="5",
            holidays="$H$2:$H$10"
        )
        # WORKDAY adds working days based on remaining/velocity
        # 50/5 = 10 working days
        assert formula == "=WORKDAY(2025-01-15, 50 / 5, $H$2:$H$10)"


class TestCompletionProbability:
    """Test completion probability calculations."""

    def test_completion_probability_normal_distribution(self, formula_templates):
        """Test probability of completing by target date."""
        formula = formula_templates.apply_template(
            "completion_probability",
            target_date="45000",
            forecast_date="45010",
            forecast_std_dev="5"
        )
        # NORM.DIST for cumulative probability
        assert formula == "=NORM.DIST(45000, 45010, 5, TRUE)"

    def test_completion_probability_high_confidence(self, formula_templates):
        """Test probability with target after forecast (high confidence)."""
        formula = formula_templates.apply_template(
            "completion_probability",
            target_date="45020",
            forecast_date="45010",
            forecast_std_dev="3"
        )
        # Target > forecast = high probability
        assert "45020" in formula and "45010" in formula


class TestStoryPointConversion:
    """Test story point to hours conversion formulas."""

    def test_story_points_to_hours(self, formula_templates):
        """Test converting story points to estimated hours."""
        formula = formula_templates.apply_template(
            "story_point_to_hours",
            story_points="8",
            hours_per_point="6"
        )
        # 8 points * 6 hours/point = 48 hours
        assert formula == "=8 * 6"

    def test_hours_to_story_points(self, formula_templates):
        """Test converting hours to story points."""
        formula = formula_templates.apply_template(
            "hours_to_story_points",
            hours="48",
            hours_per_point="6"
        )
        # 48 hours / 6 hours/point = 8 points
        assert "48" in formula and "6" in formula and "IF" in formula

    def test_hours_to_story_points_zero_divisor(self, formula_templates):
        """Test hours to story points with zero hours per point."""
        formula = formula_templates.apply_template(
            "hours_to_story_points",
            hours="48",
            hours_per_point="0"
        )
        # Returns 0 to avoid division by zero
        assert "IF" in formula and "=0" in formula


class TestCycleTimeAndLeadTime:
    """Test cycle time and lead time calculations."""

    def test_cycle_time_average(self, formula_templates):
        """Test average cycle time calculation."""
        formula = formula_templates.apply_template(
            "cycle_time_average",
            cycle_time_range="$B$2:$B$100"
        )
        # AVERAGE of cycle times
        assert formula == "=AVERAGE($B$2:$B$100)"

    def test_lead_time_average(self, formula_templates):
        """Test average lead time calculation."""
        formula = formula_templates.apply_template(
            "lead_time_average",
            lead_time_range="$C$2:$C$100"
        )
        # AVERAGE of lead times
        assert formula == "=AVERAGE($C$2:$C$100)"


class TestThroughput:
    """Test throughput calculation formulas."""

    def test_throughput_sprint(self, formula_templates):
        """Test throughput for a sprint period."""
        formula = formula_templates.apply_template(
            "throughput",
            completion_date_column="$A$2:$A$100",
            period_start="2025-01-01",
            period_end="2025-01-14"
        )
        # COUNT items completed in date range
        assert 'COUNTIF($A$2:$A$100, ">="&2025-01-01)' in formula
        assert 'COUNTIF($A$2:$A$100, ">"&2025-01-14)' in formula

    def test_throughput_month(self, formula_templates):
        """Test throughput for a monthly period."""
        formula = formula_templates.apply_template(
            "throughput",
            completion_date_column="A:A",
            period_start="2025-01-01",
            period_end="2025-01-31"
        )
        # Monthly throughput calculation
        assert "2025-01-01" in formula and "2025-01-31" in formula


class TestCumulativeFlowDiagram:
    """Test cumulative flow diagram (CFD) calculations."""

    def test_cumulative_flow_wip(self, formula_templates):
        """Test Work In Progress calculation for CFD."""
        formula = formula_templates.apply_template(
            "cumulative_flow_wip",
            start_date_column="$B$2:$B$100",
            end_date_column="$C$2:$C$100",
            current_date="2025-01-15"
        )
        # COUNTIFS items started but not finished + items started but no end date
        assert "COUNTIFS" in formula
        assert "2025-01-15" in formula

    def test_cumulative_flow_wip_dynamic(self, formula_templates):
        """Test WIP calculation with dynamic current date."""
        formula = formula_templates.apply_template(
            "cumulative_flow_wip",
            start_date_column="B:B",
            end_date_column="C:C",
            current_date="TODAY()"
        )
        # Dynamic WIP using TODAY()
        assert "TODAY()" in formula


class TestExtensionHooks:
    """Test that extension hooks for advanced analytics are documented."""

    def test_predictive_analytics_hook(self, formula_templates):
        """Test predictive analytics extension hook."""
        template_data = formula_templates.get_template_data("progress")
        hooks = template_data.get("_extension_hooks", {})

        assert "predictive_analytics" in hooks
        hook = hooks["predictive_analytics"]
        assert "description" in hook
        # Check for machine learning, prediction, or forecasting keywords
        desc_lower = hook["description"].lower()
        has_prediction_term = any(term in desc_lower for term in ["machine learning", "prediction", "forecast", "time series"])
        assert has_prediction_term, f"Expected prediction-related terms in description: {hook['description']}"

    def test_adaptive_forecasting_hook(self, formula_templates):
        """Test adaptive forecasting extension hook."""
        template_data = formula_templates.get_template_data("progress")
        hooks = template_data.get("_extension_hooks", {})

        assert "adaptive_forecasting" in hooks
        hook = hooks["adaptive_forecasting"]
        assert "implementation_guide" in hook
        assert "parameters" in hook


class TestRealWorldScenarios:
    """Test with realistic project scenarios."""

    def test_two_week_sprint_burndown(self, formula_templates):
        """Test realistic 2-week sprint burndown."""
        # Sprint: 100 story points, 10 working days
        # Day 5: ideal burndown = 100 - ((100/10) * 5) = 50 points remaining
        ideal = formula_templates.apply_template(
            "burndown_ideal",
            total_work="100",
            total_days="10",
            days_elapsed="5"
        )
        assert ideal == "=100 - ((100 / 10) * 5)"

    def test_team_velocity_tracking(self, formula_templates):
        """Test realistic team velocity tracking over 6 sprints."""
        # Sprints 1-6 with velocities: 20, 25, 28, 30, 32, 35
        # Average = (20+25+28+30+32+35)/6 = 28.33
        # Trend = positive (improving)
        avg = formula_templates.apply_template(
            "velocity_average",
            sprint_velocity_range="$B$2:$B$7"
        )
        assert avg == "=AVERAGE($B$2:$B$7)"

    def test_sprint_capacity_planning(self, formula_templates):
        """Test sprint capacity for planning."""
        # Team: 6 developers, 10-day sprint, 8 hours/day, 70% focus factor
        # Capacity = 6 * 10 * 8 * 0.7 = 336 hours
        capacity = formula_templates.apply_template(
            "sprint_capacity",
            team_size="6",
            days_per_sprint="10",
            hours_per_day="8",
            focus_factor="0.7"
        )
        assert capacity == "=6 * 10 * 8 * 0.7"

    def test_commitment_tracking(self, formula_templates):
        """Test commitment vs actual delivery tracking."""
        # Committed: 50 points, Delivered: 48 points
        # Ratio = (48/50) * 100 = 96%
        ratio = formula_templates.apply_template(
            "sprint_commitment_ratio",
            actual_completed="48",
            sprint_commitment="50"
        )
        assert ratio == "=(48 / 50) * 100"

    def test_completion_forecast_scenario(self, formula_templates):
        """Test realistic completion date forecast."""
        # Current date: Jan 15, Remaining work: 60 hours, Velocity: 5 hours/day
        # Forecast: WORKDAY(Jan 15, 60/5) = WORKDAY(Jan 15, 12) = ~Feb 2
        forecast = formula_templates.apply_template(
            "completion_forecast_date",
            current_date="2025-01-15",
            remaining_work="60",
            velocity="5",
            holidays="$H$2:$H$10"
        )
        assert "60 / 5" in forecast
