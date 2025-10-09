"""Tests for Earned Value Management (EVM) formulas."""

import pytest
from app.excel.components.formulas import FormulaTemplate


class TestEarnedValueFormulas:
    """Test EVM calculation formulas."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_planned_value_formula(self, formula_templates):
        """Test Planned Value (PV) calculation."""
        formula = formula_templates.apply_template(
            "planned_value",
            budget_at_completion="100000",
            planned_percent_complete="50",
        )

        expected = "=100000 * (50 / 100)"
        assert formula == expected

    def test_earned_value_formula(self, formula_templates):
        """Test Earned Value (EV) calculation."""
        formula = formula_templates.apply_template(
            "earned_value",
            budget_at_completion="100000",
            actual_percent_complete="45",
        )

        expected = "=100000 * (45 / 100)"
        assert formula == expected

    def test_actual_cost_formula(self, formula_templates):
        """Test Actual Cost (AC) calculation."""
        formula = formula_templates.apply_template(
            "actual_cost",
            actual_costs_range="J2:J50",
        )

        expected = "=SUM(J2:J50)"
        assert formula == expected

    def test_cost_variance_formula(self, formula_templates):
        """Test Cost Variance (CV) calculation."""
        formula = formula_templates.apply_template(
            "cost_variance",
            earned_value="B10",
            actual_cost="C10",
        )

        expected = "=B10 - C10"
        assert formula == expected

    def test_schedule_variance_ev_formula(self, formula_templates):
        """Test Schedule Variance (SV) calculation."""
        formula = formula_templates.apply_template(
            "schedule_variance_ev",
            earned_value="B10",
            planned_value="A10",
        )

        expected = "=B10 - A10"
        assert formula == expected

    def test_cost_performance_index_formula(self, formula_templates):
        """Test Cost Performance Index (CPI) calculation."""
        formula = formula_templates.apply_template(
            "cost_performance_index",
            earned_value="B10",
            actual_cost="C10",
        )

        assert "IF(C10=0" in formula  # Division by zero protection
        assert "B10 / C10" in formula

    def test_schedule_performance_index_formula(self, formula_templates):
        """Test Schedule Performance Index (SPI) calculation."""
        formula = formula_templates.apply_template(
            "schedule_performance_index",
            earned_value="B10",
            planned_value="A10",
        )

        assert "IF(A10=0" in formula
        assert "B10 / A10" in formula

    def test_estimate_at_completion_formula(self, formula_templates):
        """Test Estimate at Completion (EAC) calculation."""
        formula = formula_templates.apply_template(
            "estimate_at_completion",
            budget_at_completion="D10",
            cpi="F10",
        )

        assert "IF(F10=0" in formula
        assert "D10 / F10" in formula

    def test_estimate_to_complete_formula(self, formula_templates):
        """Test Estimate to Complete (ETC) calculation."""
        formula = formula_templates.apply_template(
            "estimate_to_complete",
            estimate_at_completion="G10",
            actual_cost="C10",
        )

        expected = "=G10 - C10"
        assert formula == expected

    def test_variance_at_completion_formula(self, formula_templates):
        """Test Variance at Completion (VAC) calculation."""
        formula = formula_templates.apply_template(
            "variance_at_completion",
            budget_at_completion="D10",
            estimate_at_completion="G10",
        )

        expected = "=D10 - G10"
        assert formula == expected

    def test_to_complete_performance_index_formula(self, formula_templates):
        """Test To-Complete Performance Index (TCPI) calculation."""
        formula = formula_templates.apply_template(
            "to_complete_performance_index",
            budget_at_completion="D10",
            earned_value="B10",
            actual_cost="C10",
        )

        assert "IF(D10 - C10 = 0" in formula
        assert "(D10 - B10) / (D10 - C10)" in formula

    def test_percent_spent_formula(self, formula_templates):
        """Test percentage of budget spent calculation."""
        formula = formula_templates.apply_template(
            "percent_spent",
            actual_cost="C10",
            budget_at_completion="D10",
        )

        assert "IF(D10=0" in formula
        assert "(C10 / D10) * 100" in formula

    def test_percent_complete_formula_ev(self, formula_templates):
        """Test percentage complete based on earned value."""
        formula = formula_templates.apply_template(
            "percent_complete_formula",
            earned_value="B10",
            budget_at_completion="D10",
        )

        assert "IF(D10=0" in formula
        assert "(B10 / D10) * 100" in formula


class TestEarnedValueScenarios:
    """Test EVM scenarios with realistic project data."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_project_under_budget_scenario(self, formula_templates):
        """Test EVM indicators for under-budget project."""
        # EV = $50k, AC = $45k (spent less than earned)
        cost_variance = formula_templates.apply_template(
            "cost_variance",
            earned_value="50000",
            actual_cost="45000",
        )

        # CV = 50000 - 45000 = 5000 (positive = good)
        assert "50000 - 45000" in cost_variance

        cpi = formula_templates.apply_template(
            "cost_performance_index",
            earned_value="50000",
            actual_cost="45000",
        )

        # CPI = 50000/45000 = 1.11 (>1 = good)
        assert "50000 / 45000" in cpi

    def test_project_over_budget_scenario(self, formula_templates):
        """Test EVM indicators for over-budget project."""
        # EV = $50k, AC = $60k (spent more than earned)
        cost_variance = formula_templates.apply_template(
            "cost_variance",
            earned_value="50000",
            actual_cost="60000",
        )

        # CV = 50000 - 60000 = -10000 (negative = bad)
        assert "50000 - 60000" in cost_variance

        cpi = formula_templates.apply_template(
            "cost_performance_index",
            earned_value="50000",
            actual_cost="60000",
        )

        # CPI = 50000/60000 = 0.83 (<1 = bad)
        assert "50000 / 60000" in cpi

    def test_project_ahead_of_schedule_scenario(self, formula_templates):
        """Test EVM indicators for ahead-of-schedule project."""
        # EV = $50k, PV = $45k (earned more than planned)
        schedule_variance = formula_templates.apply_template(
            "schedule_variance_ev",
            earned_value="50000",
            planned_value="45000",
        )

        # SV = 50000 - 45000 = 5000 (positive = good)
        assert "50000 - 45000" in schedule_variance

        spi = formula_templates.apply_template(
            "schedule_performance_index",
            earned_value="50000",
            planned_value="45000",
        )

        # SPI = 50000/45000 = 1.11 (>1 = good)
        assert "50000 / 45000" in spi

    def test_project_behind_schedule_scenario(self, formula_templates):
        """Test EVM indicators for behind-schedule project."""
        # EV = $40k, PV = $50k (earned less than planned)
        schedule_variance = formula_templates.apply_template(
            "schedule_variance_ev",
            earned_value="40000",
            planned_value="50000",
        )

        # SV = 40000 - 50000 = -10000 (negative = bad)
        assert "40000 - 50000" in schedule_variance

        spi = formula_templates.apply_template(
            "schedule_performance_index",
            earned_value="40000",
            planned_value="50000",
        )

        # SPI = 40000/50000 = 0.8 (<1 = bad)
        assert "40000 / 50000" in spi

    def test_estimate_at_completion_with_poor_performance(self, formula_templates):
        """Test EAC when project is performing poorly."""
        # BAC = $100k, CPI = 0.8 (overrunning)
        eac = formula_templates.apply_template(
            "estimate_at_completion",
            budget_at_completion="100000",
            cpi="0.8",
        )

        # EAC = 100000 / 0.8 = 125000 (will overrun by $25k)
        assert "100000 / 0.8" in eac

    def test_estimate_at_completion_with_good_performance(self, formula_templates):
        """Test EAC when project is performing well."""
        # BAC = $100k, CPI = 1.2 (underrunning)
        eac = formula_templates.apply_template(
            "estimate_at_completion",
            budget_at_completion="100000",
            cpi="1.2",
        )

        # EAC = 100000 / 1.2 = 83333 (will underrun by ~$17k)
        assert "100000 / 1.2" in eac

    def test_tcpi_for_troubled_project(self, formula_templates):
        """Test TCPI when project needs improvement."""
        # BAC = $100k, EV = $40k, AC = $50k
        # Work remaining = $60k, budget remaining = $50k
        tcpi = formula_templates.apply_template(
            "to_complete_performance_index",
            budget_at_completion="100000",
            earned_value="40000",
            actual_cost="50000",
        )

        # TCPI = (100000-40000)/(100000-50000) = 60000/50000 = 1.2
        # Need CPI of 1.2 to finish on budget
        assert "(100000 - 40000) / (100000 - 50000)" in tcpi


class TestEarnedValueEdgeCases:
    """Test edge cases in EVM calculations."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_cpi_with_zero_actual_cost(self, formula_templates):
        """Test CPI doesn't cause division by zero."""
        formula = formula_templates.apply_template(
            "cost_performance_index",
            earned_value="B10",
            actual_cost="0",
        )

        # Should return 1 if AC is zero (no cost incurred yet)
        assert "IF(0=0, 1," in formula

    def test_spi_with_zero_planned_value(self, formula_templates):
        """Test SPI doesn't cause division by zero."""
        formula = formula_templates.apply_template(
            "schedule_performance_index",
            earned_value="B10",
            planned_value="0",
        )

        # Should return 1 if PV is zero
        assert "IF(0=0, 1," in formula

    def test_eac_with_zero_cpi(self, formula_templates):
        """Test EAC doesn't cause division by zero."""
        formula = formula_templates.apply_template(
            "estimate_at_completion",
            budget_at_completion="D10",
            cpi="0",
        )

        # Should return BAC if CPI is zero
        assert "IF(0=0, D10," in formula

    def test_percent_spent_with_zero_budget(self, formula_templates):
        """Test percent spent with zero budget."""
        formula = formula_templates.apply_template(
            "percent_spent",
            actual_cost="C10",
            budget_at_completion="0",
        )

        # Should return 0 if budget is zero
        assert "IF(0=0, 0," in formula

    def test_percent_complete_with_zero_budget(self, formula_templates):
        """Test percent complete with zero budget."""
        formula = formula_templates.apply_template(
            "percent_complete_formula",
            earned_value="B10",
            budget_at_completion="0",
        )

        # Should return 0 if BAC is zero
        assert "IF(0=0, 0," in formula

    def test_tcpi_when_budget_consumed(self, formula_templates):
        """Test TCPI when entire budget is already spent."""
        formula = formula_templates.apply_template(
            "to_complete_performance_index",
            budget_at_completion="100000",
            earned_value="B10",
            actual_cost="100000",  # All budget spent
        )

        # BAC - AC = 0, should return 1 to avoid division by zero
        assert "IF(100000 - 100000 = 0, 1," in formula

    def test_variance_calculations_with_equal_values(self, formula_templates):
        """Test variance formulas when values are equal."""
        # CV when EV = AC (on budget)
        cv = formula_templates.apply_template(
            "cost_variance",
            earned_value="50000",
            actual_cost="50000",
        )
        assert "50000 - 50000" in cv  # Should equal 0

        # SV when EV = PV (on schedule)
        sv = formula_templates.apply_template(
            "schedule_variance_ev",
            earned_value="50000",
            planned_value="50000",
        )
        assert "50000 - 50000" in sv  # Should equal 0
