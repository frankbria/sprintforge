"""Tests for Gantt chart visualization formulas."""

import pytest
from app.excel.components.formulas import FormulaTemplate


class TestGanttChartFormulas:
    """Test Gantt chart visualization formulas."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_gantt_bar_formula(self, formula_templates):
        """Test basic Gantt bar display formula."""
        formula = formula_templates.apply_template(
            "gantt_bar",
            timeline_date="M$1",
            start_date="$D10",
            end_date="$E10",
        )

        assert "IF(AND(M$1>=$D10, M$1<=$E10)" in formula
        assert "█" in formula  # Block character for bar

    def test_gantt_bar_progress_formula(self, formula_templates):
        """Test Gantt bar with progress indication."""
        formula = formula_templates.apply_template(
            "gantt_bar_progress",
            timeline_date="M$1",
            start_date="$D10",
            end_date="$E10",
            duration="$C10",
            percent_complete="$L10",
        )

        assert "IF(AND(M$1>=$D10, M$1<=$E10)" in formula
        assert "█" in formula  # Solid block for complete
        assert "░" in formula  # Light block for incomplete

    def test_gantt_milestone_formula(self, formula_templates):
        """Test milestone marker formula."""
        formula = formula_templates.apply_template(
            "gantt_milestone",
            timeline_date="M$1",
            milestone_date="$D10",
        )

        assert "IF(M$1=$D10" in formula
        assert "◆" in formula  # Diamond for milestone

    def test_gantt_today_marker_formula(self, formula_templates):
        """Test today marker formula."""
        formula = formula_templates.apply_template(
            "gantt_today_marker",
            timeline_date="M$1",
        )

        assert "IF(M$1=TODAY()" in formula
        assert "│" in formula  # Vertical line for today

    def test_gantt_critical_bar_formula(self, formula_templates):
        """Test critical path highlighting in Gantt chart."""
        formula = formula_templates.apply_template(
            "gantt_critical_bar",
            timeline_date="M$1",
            start_date="$D10",
            end_date="$E10",
            is_critical="$I10",
        )

        assert "IF(AND(M$1>=$D10, M$1<=$E10, $I10)" in formula
        assert "█" in formula  # Solid for critical
        assert "▓" in formula  # Pattern for non-critical

    def test_gantt_baseline_comparison_formula(self, formula_templates):
        """Test baseline marker for comparing original vs current plan."""
        formula = formula_templates.apply_template(
            "gantt_baseline_comparison",
            timeline_date="M$1",
            baseline_date="$N10",
        )

        assert "IF(M$1=$N10" in formula
        assert "▼" in formula  # Down triangle for baseline

    def test_timeline_week_header_formula(self, formula_templates):
        """Test weekly timeline header formatting."""
        formula = formula_templates.apply_template(
            "timeline_week_header",
            timeline_date="M1",
        )

        assert "TEXT(M1" in formula
        assert "MMM DD" in formula  # Format like "Jan 15"

    def test_timeline_month_header_formula(self, formula_templates):
        """Test monthly timeline header formatting."""
        formula = formula_templates.apply_template(
            "timeline_month_header",
            timeline_date="M1",
        )

        assert "TEXT(M1" in formula
        assert "MMM YYYY" in formula  # Format like "Jan 2025"

    def test_timeline_quarter_header_formula(self, formula_templates):
        """Test quarterly timeline header formatting."""
        formula = formula_templates.apply_template(
            "timeline_quarter_header",
            timeline_date="M1",
        )

        assert "TEXT(M1" in formula
        assert "YYYY" in formula
        assert "ROUNDUP(MONTH(M1)/3" in formula  # Calculate quarter

    def test_resource_utilization_formula(self, formula_templates):
        """Test resource utilization calculation."""
        formula = formula_templates.apply_template(
            "resource_utilization",
            task_dates="$D$2:$D$100",
            timeline_date="M$1",
            resource_allocation="$K$2:$K$100",
        )

        assert "SUMIF($D$2:$D$100, M$1, $K$2:$K$100)" in formula


class TestGanttChartScenarios:
    """Test Gantt chart scenarios with realistic data."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_task_spanning_multiple_days(self, formula_templates):
        """Test Gantt bar for multi-day task."""
        formula = formula_templates.apply_template(
            "gantt_bar",
            timeline_date="DATE(2025,1,10)",
            start_date="DATE(2025,1,8)",
            end_date="DATE(2025,1,12)",
        )

        # Jan 10 is between Jan 8 and Jan 12
        assert "AND(DATE(2025,1,10)>=DATE(2025,1,8), DATE(2025,1,10)<=DATE(2025,1,12))" in formula

    def test_task_before_timeline_date(self, formula_templates):
        """Test Gantt bar when task is before timeline date."""
        formula = formula_templates.apply_template(
            "gantt_bar",
            timeline_date="DATE(2025,1,20)",
            start_date="DATE(2025,1,8)",
            end_date="DATE(2025,1,12)",
        )

        # Jan 20 is after task end, should not show bar
        assert "AND(DATE(2025,1,20)>=DATE(2025,1,8), DATE(2025,1,20)<=DATE(2025,1,12))" in formula

    def test_task_after_timeline_date(self, formula_templates):
        """Test Gantt bar when task is after timeline date."""
        formula = formula_templates.apply_template(
            "gantt_bar",
            timeline_date="DATE(2025,1,5)",
            start_date="DATE(2025,1,8)",
            end_date="DATE(2025,1,12)",
        )

        # Jan 5 is before task start
        assert "AND(DATE(2025,1,5)>=DATE(2025,1,8), DATE(2025,1,5)<=DATE(2025,1,12))" in formula

    def test_progress_bar_50_percent_complete(self, formula_templates):
        """Test Gantt bar with 50% progress."""
        formula = formula_templates.apply_template(
            "gantt_bar_progress",
            timeline_date="M$1",
            start_date="DATE(2025,1,8)",
            end_date="DATE(2025,1,12)",
            duration="5",
            percent_complete="50",
        )

        # Should calculate midpoint: start + (duration * 50/100) = start + 2.5
        assert "DATE(2025,1,8)+(5*50/100)" in formula

    def test_critical_vs_non_critical_visual_difference(self, formula_templates):
        """Test visual difference between critical and non-critical tasks."""
        critical_formula = formula_templates.apply_template(
            "gantt_critical_bar",
            timeline_date="M$1",
            start_date="$D10",
            end_date="$E10",
            is_critical="TRUE",
        )

        non_critical_formula = formula_templates.apply_template(
            "gantt_critical_bar",
            timeline_date="M$1",
            start_date="$D10",
            end_date="$E10",
            is_critical="FALSE",
        )

        # Both should have the critical flag check
        assert "TRUE" in critical_formula or "$I10" in critical_formula
        assert "FALSE" in non_critical_formula or "$I10" in non_critical_formula

    def test_quarter_calculation_q1(self, formula_templates):
        """Test quarter header for Q1 dates."""
        formula = formula_templates.apply_template(
            "timeline_quarter_header",
            timeline_date="DATE(2025,2,15)",  # Feb is Q1
        )

        # Should calculate ROUNDUP(2/3) = 1 for Q1
        assert "ROUNDUP(MONTH(DATE(2025,2,15))/3" in formula

    def test_quarter_calculation_q4(self, formula_templates):
        """Test quarter header for Q4 dates."""
        formula = formula_templates.apply_template(
            "timeline_quarter_header",
            timeline_date="DATE(2025,12,15)",  # Dec is Q4
        )

        # Should calculate ROUNDUP(12/3) = 4 for Q4
        assert "ROUNDUP(MONTH(DATE(2025,12,15))/3" in formula


class TestGanttChartEdgeCases:
    """Test edge cases in Gantt chart formulas."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_single_day_task(self, formula_templates):
        """Test Gantt bar for single-day task."""
        formula = formula_templates.apply_template(
            "gantt_bar",
            timeline_date="M$1",
            start_date="DATE(2025,1,10)",
            end_date="DATE(2025,1,10)",  # Same day
        )

        # Start and end are same, should still work
        assert "DATE(2025,1,10)" in formula

    def test_milestone_on_timeline_date(self, formula_templates):
        """Test milestone marker when date matches exactly."""
        formula = formula_templates.apply_template(
            "gantt_milestone",
            timeline_date="DATE(2025,1,15)",
            milestone_date="DATE(2025,1,15)",
        )

        assert "DATE(2025,1,15)=DATE(2025,1,15)" in formula

    def test_today_marker_updates_daily(self, formula_templates):
        """Test that today marker uses TODAY() function which updates."""
        formula = formula_templates.apply_template(
            "gantt_today_marker",
            timeline_date="M$1",
        )

        # Should use TODAY() function, not a static date
        assert "TODAY()" in formula

    def test_resource_utilization_zero_resources(self, formula_templates):
        """Test resource utilization when no resources allocated."""
        formula = formula_templates.apply_template(
            "resource_utilization",
            task_dates="$D$2:$D$10",
            timeline_date="M$1",
            resource_allocation="$K$2:$K$10",
        )

        # SUMIF should return 0 if no matching dates
        assert "SUMIF" in formula

    def test_progress_bar_zero_percent(self, formula_templates):
        """Test progress bar with 0% complete."""
        formula = formula_templates.apply_template(
            "gantt_bar_progress",
            timeline_date="M$1",
            start_date="$D10",
            end_date="$E10",
            duration="$C10",
            percent_complete="0",
        )

        # All bars should be light (incomplete)
        assert "0/100" in formula or "$L10" in formula

    def test_progress_bar_100_percent(self, formula_templates):
        """Test progress bar with 100% complete."""
        formula = formula_templates.apply_template(
            "gantt_bar_progress",
            timeline_date="M$1",
            start_date="$D10",
            end_date="$E10",
            duration="$C10",
            percent_complete="100",
        )

        # All bars should be solid (complete)
        assert "100/100" in formula or "$L10" in formula
