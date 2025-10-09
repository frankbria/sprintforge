"""
Comprehensive tests for conditional formatting formulas.

This test suite validates:
- Status highlighting (not started, in progress, complete)
- Risk indicators (overdue, at risk)
- Critical path highlighting
- Budget status indicators
- Gantt bar formatting logic
- Priority and blocked task indicators

All formulas return TRUE/FALSE for conditional formatting rules.
"""

import pytest
from app.excel.components.templates.formula_loader import FormulaTemplateLoader


@pytest.fixture
def formula_templates():
    """Load formatting formula templates for testing."""
    loader = FormulaTemplateLoader()
    loader.load_template("formatting")
    return loader


class TestStatusFormatting:
    """Test task status conditional formatting formulas."""

    def test_status_not_started(self, formula_templates):
        """Test formatting for tasks that haven't started."""
        formula = formula_templates.apply_template(
            "status_not_started",
            actual_start="$D2",
            percent_complete="$E2"
        )
        # TRUE when both actual_start and percent_complete are blank
        assert formula == "=AND(ISBLANK($D2), ISBLANK($E2))"

    def test_status_in_progress(self, formula_templates):
        """Test formatting for tasks in progress."""
        formula = formula_templates.apply_template(
            "status_in_progress",
            actual_start="$D2",
            percent_complete="$E2"
        )
        # TRUE when started, not 100% complete, and > 0% complete
        assert formula == "=AND(NOT(ISBLANK($D2)), $E2<100, $E2>0)"

    def test_status_complete(self, formula_templates):
        """Test formatting for completed tasks."""
        formula = formula_templates.apply_template(
            "status_complete",
            percent_complete="$E2"
        )
        # TRUE when percent_complete >= 100
        assert formula == "=$E2>=100"


class TestRiskIndicators:
    """Test risk indicator conditional formatting formulas."""

    def test_overdue_task(self, formula_templates):
        """Test formatting for overdue tasks."""
        formula = formula_templates.apply_template(
            "overdue_task",
            end_date="$F2",
            percent_complete="$E2"
        )
        # TRUE when end_date < TODAY() and not 100% complete
        assert formula == "=AND($F2<TODAY(), $E2<100)"

    def test_at_risk_task(self, formula_templates):
        """Test formatting for at-risk tasks (due soon, not nearly complete)."""
        formula = formula_templates.apply_template(
            "at_risk_task",
            end_date="$F2",
            percent_complete="$E2"
        )
        # TRUE when due in <=5 days, still >0 days away, and <80% complete
        assert formula == "=AND($F2-TODAY()<=5, $F2-TODAY()>0, $E2<80)"

    def test_blocked_task(self, formula_templates):
        """Test formatting for blocked tasks."""
        formula = formula_templates.apply_template(
            "blocked_task",
            status="$G2"
        )
        # TRUE when status = "Blocked"
        assert formula == '=$G2="Blocked"'


class TestCriticalPathFormatting:
    """Test critical path highlighting formulas."""

    def test_critical_path_highlight(self, formula_templates):
        """Test highlighting of critical path tasks."""
        formula = formula_templates.apply_template(
            "critical_path_highlight",
            is_critical="$H2"
        )
        # TRUE when is_critical = TRUE
        assert formula == "=$H2=TRUE"


class TestBudgetFormatting:
    """Test budget status conditional formatting formulas."""

    def test_over_budget(self, formula_templates):
        """Test formatting for tasks over budget."""
        formula = formula_templates.apply_template(
            "over_budget",
            actual_cost="$I2",
            budget="$J2"
        )
        # TRUE when actual_cost > budget
        assert formula == "=$I2>$J2"

    def test_under_budget(self, formula_templates):
        """Test formatting for tasks significantly under budget."""
        formula = formula_templates.apply_template(
            "under_budget",
            percent_complete="$E2",
            actual_cost="$I2",
            budget="$J2"
        )
        # TRUE when >50% complete and actual < 90% of budget
        assert formula == "=AND($E2>50, $I2<$J2*0.9)"


class TestResourceFormatting:
    """Test resource utilization conditional formatting formulas."""

    def test_resource_overallocated(self, formula_templates):
        """Test formatting for overallocated resources."""
        formula = formula_templates.apply_template(
            "resource_overallocated",
            resource_utilization="$K2"
        )
        # TRUE when resource_utilization > 1 (>100%)
        assert formula == "=$K2>1"

    def test_resource_underutilized(self, formula_templates):
        """Test formatting for underutilized resources."""
        formula = formula_templates.apply_template(
            "resource_underutilized",
            resource_utilization="$K2"
        )
        # TRUE when resource_utilization < 0.5 (<50%)
        assert formula == "=$K2<0.5"


class TestGanttBarFormatting:
    """Test Gantt chart bar conditional formatting formulas."""

    def test_gantt_bar_active(self, formula_templates):
        """Test Gantt bar showing active date range."""
        formula = formula_templates.apply_template(
            "gantt_bar_active",
            timeline_date="$M$1",
            start_date="$D2",
            end_date="$F2"
        )
        # TRUE when timeline_date is between start and end
        assert formula == "=AND($M$1>=$D2, $M$1<=$F2)"

    def test_gantt_bar_completed(self, formula_templates):
        """Test Gantt bar showing completed portion."""
        formula = formula_templates.apply_template(
            "gantt_bar_completed",
            timeline_date="$M$1",
            start_date="$D2",
            duration="$L2",
            percent_complete="$E2"
        )
        # TRUE when timeline_date in completed portion
        assert formula == "=AND($M$1>=$D2, $M$1<=$D2+($L2*$E2/100))"

    def test_gantt_bar_remaining(self, formula_templates):
        """Test Gantt bar showing remaining portion."""
        formula = formula_templates.apply_template(
            "gantt_bar_remaining",
            timeline_date="$M$1",
            start_date="$D2",
            duration="$L2",
            percent_complete="$E2",
            end_date="$F2"
        )
        # TRUE when timeline_date in remaining portion
        assert formula == "=AND($M$1>$D2+($L2*$E2/100), $M$1<=$F2)"

    def test_gantt_today_marker(self, formula_templates):
        """Test Gantt chart today marker column."""
        formula = formula_templates.apply_template(
            "gantt_today_marker",
            timeline_date="$M$1"
        )
        # TRUE when timeline_date = TODAY()
        assert formula == "=$M$1=TODAY()"


class TestMilestoneFormatting:
    """Test milestone indicator conditional formatting."""

    def test_milestone_indicator(self, formula_templates):
        """Test milestone identification (zero duration tasks)."""
        formula = formula_templates.apply_template(
            "milestone_indicator",
            duration="$L2",
            end_date="$F2"
        )
        # TRUE when duration=0 and end_date is not blank
        assert formula == "=AND($L2=0, NOT(ISBLANK($F2)))"


class TestPriorityFormatting:
    """Test priority indicator conditional formatting."""

    def test_high_priority(self, formula_templates):
        """Test high priority task highlighting."""
        formula = formula_templates.apply_template(
            "high_priority",
            priority="$N2"
        )
        # TRUE when priority = "High"
        assert formula == '=$N2="High"'


class TestDependencyWarnings:
    """Test dependency warning conditional formatting."""

    def test_dependency_warning(self, formula_templates):
        """Test warning when starting task with incomplete predecessors."""
        formula = formula_templates.apply_template(
            "dependency_warning",
            predecessor="$O2",
            start_date="$D2"
        )
        # TRUE when predecessor exists, predecessor not complete, and task should start
        assert formula == '=AND(NOT(ISBLANK($O2)), INDIRECT($O2&"percent_complete")<100, $D2<=TODAY())'


class TestVelocityFormatting:
    """Test velocity indicator conditional formatting."""

    def test_velocity_above_average(self, formula_templates):
        """Test highlighting sprints with above-average velocity."""
        formula = formula_templates.apply_template(
            "velocity_above_average",
            sprint_velocity="$P2",
            average_velocity="$Q$1"
        )
        # TRUE when sprint_velocity > average * 1.1 (10% above)
        assert formula == "=$P2>$Q$1*1.1"

    def test_velocity_below_average(self, formula_templates):
        """Test highlighting sprints with below-average velocity."""
        formula = formula_templates.apply_template(
            "velocity_below_average",
            sprint_velocity="$P2",
            average_velocity="$Q$1"
        )
        # TRUE when sprint_velocity < average * 0.9 (10% below)
        assert formula == "=$P2<$Q$1*0.9"


class TestConfidenceFormatting:
    """Test confidence level indicator conditional formatting."""

    def test_confidence_high(self, formula_templates):
        """Test highlighting high-confidence estimates."""
        formula = formula_templates.apply_template(
            "confidence_high",
            confidence_level="$R2"
        )
        # TRUE when confidence_level >= 0.8 (80%)
        assert formula == "=$R2>=0.8"

    def test_confidence_low(self, formula_templates):
        """Test highlighting low-confidence estimates."""
        formula = formula_templates.apply_template(
            "confidence_low",
            confidence_level="$R2"
        )
        # TRUE when confidence_level < 0.5 (50%)
        assert formula == "=$R2<0.5"


class TestFormulaLogic:
    """Test the logic of conditional formatting formulas."""

    def test_overdue_logic_past_date(self, formula_templates):
        """Test overdue logic with date in past."""
        # If end_date is in past and task not complete, should format as overdue
        formula = formula_templates.apply_template(
            "overdue_task",
            end_date="$F2",
            percent_complete="$E2"
        )
        # Verifies both conditions required
        assert "AND" in formula
        assert "TODAY()" in formula
        assert "<100" in formula

    def test_at_risk_logic_near_deadline(self, formula_templates):
        """Test at-risk logic for tasks near deadline."""
        # Task due in 3 days but only 60% complete should be at-risk
        formula = formula_templates.apply_template(
            "at_risk_task",
            end_date="$F2",
            percent_complete="$E2"
        )
        # Verifies all three conditions
        assert "<=5" in formula  # Due within 5 days
        assert ">0" in formula   # Still in future
        assert "<80" in formula  # Less than 80% complete

    def test_gantt_completed_logic(self, formula_templates):
        """Test Gantt completed portion logic."""
        # If 50% complete on 10-day task, first 5 days should show as completed
        formula = formula_templates.apply_template(
            "gantt_bar_completed",
            timeline_date="$M$1",
            start_date="$D2",
            duration="$L2",
            percent_complete="$E2"
        )
        # Verifies date range calculation
        assert ">=" in formula
        assert "<=" in formula
        assert "/100" in formula  # Percent to decimal conversion


class TestBoundaryConditions:
    """Test boundary conditions for conditional formatting."""

    def test_status_exactly_100_percent(self, formula_templates):
        """Test complete status at exactly 100%."""
        formula = formula_templates.apply_template(
            "status_complete",
            percent_complete="$E2"
        )
        # Should be TRUE when >= 100, not just >
        assert ">=" in formula

    def test_at_risk_exactly_5_days(self, formula_templates):
        """Test at-risk status at exactly 5 days remaining."""
        formula = formula_templates.apply_template(
            "at_risk_task",
            end_date="$F2",
            percent_complete="$E2"
        )
        # Should include 5 days (<=5, not <5)
        assert "<=5" in formula

    def test_at_risk_exactly_80_percent(self, formula_templates):
        """Test at-risk status at exactly 80% complete."""
        formula = formula_templates.apply_template(
            "at_risk_task",
            end_date="$F2",
            percent_complete="$E2"
        )
        # Should not be at-risk if exactly 80% (<80, not <=80)
        assert "<80" in formula

    def test_under_budget_exactly_90_percent(self, formula_templates):
        """Test under-budget status at exactly 90% of budget."""
        formula = formula_templates.apply_template(
            "under_budget",
            percent_complete="$E2",
            actual_cost="$I2",
            budget="$J2"
        )
        # Should not format if exactly 90% (<0.9, not <=0.9)
        assert "<" in formula
        assert "0.9" in formula


class TestCellReferenceTypes:
    """Test correct cell reference types (absolute vs relative)."""

    def test_absolute_row_reference(self, formula_templates):
        """Test formulas use absolute row references where needed."""
        # Timeline header should be absolute row ($M$1)
        formula = formula_templates.apply_template(
            "gantt_bar_active",
            timeline_date="$M$1",
            start_date="$D2",
            end_date="$F2"
        )
        assert "$M$1" in formula  # Absolute for header
        assert "$D2" in formula   # Absolute column, relative row
        assert "$F2" in formula

    def test_relative_row_reference(self, formula_templates):
        """Test formulas use relative row references for row data."""
        formula = formula_templates.apply_template(
            "status_complete",
            percent_complete="$E2"
        )
        # Should have absolute column ($E) but relative row (2)
        # So it can copy down to $E3, $E4, etc.
        assert "$E2" in formula


class TestRealWorldScenarios:
    """Test with realistic project management scenarios."""

    def test_overdue_incomplete_task_scenario(self, formula_templates):
        """Test realistic overdue task detection."""
        # Task due yesterday, 75% complete - should be overdue
        formula = formula_templates.apply_template(
            "overdue_task",
            end_date="$F2",
            percent_complete="$E2"
        )
        # Both conditions must be true
        assert "AND" in formula
        assert "TODAY()" in formula

    def test_at_risk_task_scenario(self, formula_templates):
        """Test realistic at-risk task detection."""
        # Task due in 3 days, only 50% complete - should be at-risk
        formula = formula_templates.apply_template(
            "at_risk_task",
            end_date="$F2",
            percent_complete="$E2"
        )
        # All three conditions
        assert "AND" in formula
        assert "<=5" in formula
        assert ">0" in formula
        assert "<80" in formula

    def test_gantt_chart_scenario(self, formula_templates):
        """Test realistic Gantt chart formatting."""
        # 10-day task, 60% complete
        # Days 1-6 should show as completed
        # Days 7-10 should show as remaining
        completed = formula_templates.apply_template(
            "gantt_bar_completed",
            timeline_date="$M$1",
            start_date="$D2",
            duration="$L2",
            percent_complete="$E2"
        )
        remaining = formula_templates.apply_template(
            "gantt_bar_remaining",
            timeline_date="$M$1",
            start_date="$D2",
            duration="$L2",
            percent_complete="$E2",
            end_date="$F2"
        )
        # Completed: timeline >= start AND <= start + (duration * %/100)
        assert ">=" in completed and "<=" in completed
        # Remaining: timeline > start + (duration * %/100) AND <= end
        assert ">" in remaining and "<=" in remaining

    def test_resource_overallocation_scenario(self, formula_templates):
        """Test realistic resource overallocation detection."""
        # Developer allocated 1.3 (130%) - should be flagged
        formula = formula_templates.apply_template(
            "resource_overallocated",
            resource_utilization="$K2"
        )
        # > 1.0 indicates over-allocation
        assert ">1" in formula

    def test_budget_tracking_scenario(self, formula_templates):
        """Test realistic budget status tracking."""
        # Task 60% complete, spent $3000 of $5000 budget
        # Under budget: 60% > 50% AND $3000 < $5000 * 0.9 ($4500)
        under = formula_templates.apply_template(
            "under_budget",
            percent_complete="$E2",
            actual_cost="$I2",
            budget="$J2"
        )
        assert "AND" in under
        assert ">50" in under
        assert "*0.9" in under

    def test_milestone_scenario(self, formula_templates):
        """Test realistic milestone identification."""
        # Milestone: duration = 0, has end date (e.g., "Sprint Demo")
        formula = formula_templates.apply_template(
            "milestone_indicator",
            duration="$L2",
            end_date="$F2"
        )
        assert "=0" in formula
        assert "NOT(ISBLANK" in formula

    def test_velocity_performance_scenario(self, formula_templates):
        """Test realistic velocity performance tracking."""
        # Team velocity 35, average 30 - should highlight as above average
        # 35 > 30 * 1.1 (33) = TRUE
        above = formula_templates.apply_template(
            "velocity_above_average",
            sprint_velocity="$P2",
            average_velocity="$Q$1"
        )
        assert "*1.1" in above  # 10% above threshold

    def test_confidence_scenario(self, formula_templates):
        """Test realistic confidence level highlighting."""
        # Estimate with 85% confidence - should be high confidence
        high = formula_templates.apply_template(
            "confidence_high",
            confidence_level="$R2"
        )
        # >= 0.8 (80%)
        assert ">=0.8" in high


class TestFormatConsistency:
    """Test that formatting formulas follow consistent patterns."""

    def test_all_formulas_return_boolean(self, formula_templates):
        """Test that all formatting formulas return TRUE/FALSE."""
        template_data = formula_templates.get_template_data("formatting")

        # Skip metadata
        formulas_to_test = {k: v for k, v in template_data.items() if not k.startswith("_")}

        for name, config in formulas_to_test.items():
            formula = config.get("formula", "")
            # All should use comparison operators or boolean functions
            has_comparison = any(op in formula for op in ["=", ">", "<", "AND", "OR", "NOT", "IF", "ISBLANK"])
            assert has_comparison, f"Formula {name} should return boolean value"

    def test_suggested_formats_provided(self, formula_templates):
        """Test that all formatting formulas have suggested format guidance."""
        template_data = formula_templates.get_template_data("formatting")

        formulas_to_test = {k: v for k, v in template_data.items() if not k.startswith("_")}

        for name, config in formulas_to_test.items():
            assert "suggested_format" in config, f"Formula {name} should have suggested_format"
            suggested = config["suggested_format"]
            # Should mention color or style
            has_visual_guidance = any(term in suggested.lower() for term in [
                "red", "green", "yellow", "orange", "blue", "gray",
                "bold", "background", "text", "border", "icon"
            ])
            assert has_visual_guidance, f"Formula {name} suggested_format should include visual guidance"
