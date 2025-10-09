"""Tests for critical path method (CPM) formulas."""

import pytest
from app.excel.components.formulas import FormulaTemplate


class TestCriticalPathFormulas:
    """Test critical path calculation formulas."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_early_start_formula(self, formula_templates):
        """Test early start calculation formula."""
        formula = formula_templates.apply_template(
            "early_start",
            predecessors_early_finish="E2:E5",
            lag_days="0",
        )

        assert "MAX" in formula
        assert "E2:E5" in formula

    def test_early_finish_formula(self, formula_templates):
        """Test early finish calculation formula."""
        formula = formula_templates.apply_template(
            "early_finish",
            early_start="D10",
            duration="C10",
        )

        expected = "=D10 + C10"
        assert formula == expected

    def test_late_finish_formula(self, formula_templates):
        """Test late finish calculation formula."""
        formula = formula_templates.apply_template(
            "late_finish",
            successors_late_start="D12:D15",
            lag_days="0",
        )

        assert "MIN" in formula
        assert "D12:D15" in formula

    def test_late_start_formula(self, formula_templates):
        """Test late start calculation formula."""
        formula = formula_templates.apply_template(
            "late_start",
            late_finish="G10",
            duration="C10",
        )

        expected = "=G10 - C10"
        assert formula == expected

    def test_total_float_formula(self, formula_templates):
        """Test total float (slack) calculation."""
        formula = formula_templates.apply_template(
            "total_float",
            late_start="F10",
            early_start="D10",
        )

        expected = "=F10 - D10"
        assert formula == expected

    def test_free_float_formula(self, formula_templates):
        """Test free float calculation."""
        formula = formula_templates.apply_template(
            "free_float",
            successors_early_start="D12:D15",
            early_finish="E10",
        )

        assert "MIN" in formula
        assert "D12:D15" in formula
        assert "E10" in formula

    def test_is_critical_formula(self, formula_templates):
        """Test critical path boolean indicator."""
        formula = formula_templates.apply_template(
            "is_critical",
            total_float="H10",
            duration="C10",
        )

        assert "IF" in formula
        assert "AND" in formula
        assert "H10<=0" in formula
        assert "C10>0" in formula
        assert "TRUE" in formula
        assert "FALSE" in formula

    def test_critical_path_highlight_formula(self, formula_templates):
        """Test critical path text highlight."""
        formula = formula_templates.apply_template(
            "critical_path_highlight",
            is_critical="I10",
        )

        assert "IF" in formula
        assert "I10" in formula
        assert "CRITICAL" in formula

    def test_schedule_variance_formula(self, formula_templates):
        """Test schedule variance calculation."""
        formula = formula_templates.apply_template(
            "schedule_variance",
            actual_finish="J10",
            planned_finish="E10",
        )

        expected = "=J10 - E10"
        assert formula == expected

    def test_percent_complete_formula(self, formula_templates):
        """Test percentage complete calculation."""
        formula = formula_templates.apply_template(
            "percent_complete",
            actual_duration="K10",
            duration="C10",
        )

        assert "IF" in formula
        assert "C10=0" in formula
        assert "MIN(100" in formula
        assert "K10 / C10" in formula


class TestCriticalPathScenarios:
    """Test critical path scenarios with realistic data."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_critical_task_identification(self, formula_templates):
        """Test that tasks with zero float are identified as critical."""
        # Task with zero float
        is_critical = formula_templates.apply_template(
            "is_critical",
            total_float="0",  # Zero float
            duration="5",  # Non-zero duration
        )

        # Should evaluate to TRUE for critical task
        assert "IF(AND(0<=0, 5>0), TRUE, FALSE)" == is_critical

    def test_non_critical_task_identification(self, formula_templates):
        """Test that tasks with positive float are not critical."""
        is_critical = formula_templates.apply_template(
            "is_critical",
            total_float="3",  # Positive float
            duration="5",
        )

        # Should have condition checking for <= 0
        assert "3<=0" in is_critical

    def test_milestone_not_critical_if_zero_duration(self, formula_templates):
        """Test that milestones (zero duration) are not marked critical."""
        is_critical = formula_templates.apply_template(
            "is_critical",
            total_float="0",
            duration="0",  # Milestone has zero duration
        )

        # Should check duration > 0
        assert "0>0" in is_critical

    def test_float_calculation_chain(self, formula_templates):
        """Test complete float calculation chain."""
        # Calculate early finish
        early_finish = formula_templates.apply_template(
            "early_finish",
            early_start="D5",
            duration="5",
        )
        assert early_finish == "=D5 + 5"

        # Calculate late start
        late_start = formula_templates.apply_template(
            "late_start",
            late_finish="G5",
            duration="5",
        )
        assert late_start == "=G5 - 5"

        # Calculate total float
        total_float = formula_templates.apply_template(
            "total_float",
            late_start="F5",
            early_start="D5",
        )
        assert total_float == "=F5 - D5"

    def test_schedule_performance_positive_variance(self, formula_templates):
        """Test schedule variance for ahead-of-schedule task."""
        # Actual finish before planned = negative variance (good)
        variance = formula_templates.apply_template(
            "schedule_variance",
            actual_finish="DATE(2025,1,10)",
            planned_finish="DATE(2025,1,15)",
        )

        assert "DATE(2025,1,10) - DATE(2025,1,15)" in variance

    def test_schedule_performance_negative_variance(self, formula_templates):
        """Test schedule variance for behind-schedule task."""
        variance = formula_templates.apply_template(
            "schedule_variance",
            actual_finish="DATE(2025,1,20)",
            planned_finish="DATE(2025,1,15)",
        )

        assert "DATE(2025,1,20) - DATE(2025,1,15)" in variance


class TestCriticalPathEdgeCases:
    """Test edge cases in critical path calculations."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_percent_complete_zero_duration(self, formula_templates):
        """Test percent complete with zero duration doesn't cause division error."""
        formula = formula_templates.apply_template(
            "percent_complete",
            actual_duration="5",
            duration="0",
        )

        # Should have protection against division by zero
        assert "IF(0=0, 0," in formula

    def test_percent_complete_caps_at_100(self, formula_templates):
        """Test percent complete is capped at 100%."""
        formula = formula_templates.apply_template(
            "percent_complete",
            actual_duration="K10",
            duration="C10",
        )

        # Should use MIN to cap at 100
        assert "MIN(100," in formula

    def test_negative_float_indicates_critical(self, formula_templates):
        """Test that negative float (impossible schedule) is treated as critical."""
        is_critical = formula_templates.apply_template(
            "is_critical",
            total_float="-2",  # Negative float
            duration="5",
        )

        # Condition is <= 0, so -2 <= 0 is true
        assert "-2<=0" in is_critical

    def test_free_float_with_no_successors(self, formula_templates):
        """Test free float calculation when task has no successors."""
        formula = formula_templates.apply_template(
            "free_float",
            successors_early_start="Z999",  # Empty or far-future reference
            early_finish="E10",
        )

        assert "MIN(Z999)" in formula
        assert "E10" in formula
