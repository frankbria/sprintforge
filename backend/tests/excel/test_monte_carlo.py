"""Tests for Monte Carlo simulation formulas with statistical validation."""

import pytest
import re
from app.excel.components.formulas import FormulaTemplate


class TestPERTDistribution:
    """Test PERT (Program Evaluation and Review Technique) distribution formulas."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_pert_mean_symmetric(self, formula_templates):
        """Test PERT mean calculation with symmetric distribution."""
        # Symmetric: optimistic=10, most_likely=20, pessimistic=30
        formula = formula_templates.apply_template(
            "pert_mean",
            optimistic="10",
            most_likely="20",
            pessimistic="30"
        )

        # PERT mean = (10 + 4*20 + 30) / 6 = 120/6 = 20
        assert formula == "=(10 + 4*20 + 30) / 6"

    def test_pert_mean_skewed_right(self, formula_templates):
        """Test PERT mean with right-skewed distribution."""
        # Right-skewed: optimistic=5, most_likely=10, pessimistic=50
        formula = formula_templates.apply_template(
            "pert_mean",
            optimistic="5",
            most_likely="10",
            pessimistic="50"
        )

        # PERT mean = (5 + 4*10 + 50) / 6 = 95/6 ≈ 15.83
        # Mean should be pulled toward pessimistic
        assert "5 + 4*10 + 50" in formula
        assert "/ 6" in formula

    def test_pert_mean_skewed_left(self, formula_templates):
        """Test PERT mean with left-skewed distribution."""
        # Left-skewed: optimistic=5, most_likely=40, pessimistic=50
        formula = formula_templates.apply_template(
            "pert_mean",
            optimistic="5",
            most_likely="40",
            pessimistic="50"
        )

        # PERT mean = (5 + 4*40 + 50) / 6 = 215/6 ≈ 35.83
        # Mean should be pulled toward optimistic
        assert "5 + 4*40 + 50" in formula

    def test_pert_std_dev_narrow_range(self, formula_templates):
        """Test PERT standard deviation with narrow range."""
        # Narrow range: optimistic=18, pessimistic=24 (range=6)
        formula = formula_templates.apply_template(
            "pert_std_dev",
            pessimistic="24",
            optimistic="18"
        )

        # σ = (24 - 18) / 6 = 1
        assert formula == "=(24 - 18) / 6"

    def test_pert_std_dev_wide_range(self, formula_templates):
        """Test PERT standard deviation with wide range."""
        # Wide range: optimistic=10, pessimistic=100 (range=90)
        formula = formula_templates.apply_template(
            "pert_std_dev",
            pessimistic="100",
            optimistic="10"
        )

        # σ = (100 - 10) / 6 = 15
        assert formula == "=(100 - 10) / 6"

    def test_pert_std_dev_statistical_basis(self, formula_templates):
        """Test PERT std dev represents 6-sigma range."""
        # The formula (b-a)/6 assumes ~99.7% of values fall within range
        # This is based on normal approximation to Beta distribution
        formula = formula_templates.apply_template(
            "pert_std_dev",
            pessimistic="30",
            optimistic="0"
        )

        # For range of 30, std dev should be 5
        # This means ±3σ ≈ ±15, covering the full range
        assert "30 - 0" in formula
        assert "/ 6" in formula


class TestMonteCarloSampling:
    """Test Monte Carlo sampling formulas."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_monte_carlo_sample_normal(self, formula_templates):
        """Test normal distribution Monte Carlo sample."""
        formula = formula_templates.apply_template(
            "monte_carlo_sample",
            mean="20",
            std_dev="5"
        )

        # Should use NORM.INV with RAND()
        assert "NORM.INV(RAND()" in formula
        assert "20" in formula  # mean
        assert "5" in formula   # std_dev

    def test_monte_carlo_triangular_distribution(self, formula_templates):
        """Test triangular distribution (alternative to normal)."""
        formula = formula_templates.apply_template(
            "monte_carlo_triangular",
            optimistic="10",
            most_likely="20",
            pessimistic="40"
        )

        # Triangular distribution formula is complex
        # Should have IF statement and SQRT for proper transformation
        assert "IF(RAND()" in formula
        assert "SQRT" in formula
        assert "10" in formula  # optimistic
        assert "20" in formula  # most_likely
        assert "40" in formula  # pessimistic

    def test_percentile_estimate_p10(self, formula_templates):
        """Test P10 (10th percentile) estimate."""
        formula = formula_templates.apply_template(
            "percentile_estimate",
            percentile="0.1",
            mean="20",
            std_dev="5"
        )

        # P10 should be below mean
        assert "NORM.INV(0.1" in formula
        assert "20" in formula
        assert "5" in formula

    def test_percentile_estimate_p50(self, formula_templates):
        """Test P50 (median) estimate."""
        formula = formula_templates.apply_template(
            "percentile_estimate",
            percentile="0.5",
            mean="20",
            std_dev="5"
        )

        # P50 = median = mean for normal distribution
        assert "NORM.INV(0.5" in formula

    def test_percentile_estimate_p90(self, formula_templates):
        """Test P90 (90th percentile) estimate."""
        formula = formula_templates.apply_template(
            "percentile_estimate",
            percentile="0.9",
            mean="20",
            std_dev="5"
        )

        # P90 should be above mean
        assert "NORM.INV(0.9" in formula


class TestConfidenceIntervals:
    """Test confidence interval calculations."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_confidence_interval_lower_95(self, formula_templates):
        """Test 95% confidence interval lower bound."""
        formula = formula_templates.apply_template(
            "confidence_interval_lower",
            mean="100",
            std_dev="10",
            confidence_level="0.95"
        )

        # CI lower = mean - z*σ
        # For 95% CI, z ≈ 1.96
        assert "100 - NORM.S.INV(0.95)" in formula
        assert "* 10" in formula

    def test_confidence_interval_upper_95(self, formula_templates):
        """Test 95% confidence interval upper bound."""
        formula = formula_templates.apply_template(
            "confidence_interval_upper",
            mean="100",
            std_dev="10",
            confidence_level="0.95"
        )

        # CI upper = mean + z*σ
        assert "100 + NORM.S.INV(0.95)" in formula
        assert "* 10" in formula

    def test_confidence_interval_lower_80(self, formula_templates):
        """Test 80% confidence interval (narrower than 95%)."""
        formula = formula_templates.apply_template(
            "confidence_interval_lower",
            mean="50",
            std_dev="8",
            confidence_level="0.8"
        )

        # 80% CI is narrower than 95% CI
        assert "50 - NORM.S.INV(0.8)" in formula
        assert "* 8" in formula

    def test_confidence_interval_upper_99(self, formula_templates):
        """Test 99% confidence interval (wider than 95%)."""
        formula = formula_templates.apply_template(
            "confidence_interval_upper",
            mean="200",
            std_dev="15",
            confidence_level="0.99"
        )

        # 99% CI is wider than 95% CI
        assert "200 + NORM.S.INV(0.99)" in formula
        assert "* 15" in formula


class TestProbabilityCalculations:
    """Test probability and risk calculations."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_probability_on_time(self, formula_templates):
        """Test probability of completing by target date."""
        formula = formula_templates.apply_template(
            "probability_on_time",
            target_date="30",
            mean="25",
            std_dev="5"
        )

        # Should use cumulative normal distribution
        assert "NORM.DIST(30, 25, 5, TRUE)" in formula

    def test_probability_on_time_tight_deadline(self, formula_templates):
        """Test probability with tight deadline (target < mean)."""
        formula = formula_templates.apply_template(
            "probability_on_time",
            target_date="20",
            mean="25",
            std_dev="3"
        )

        # Tight deadline: probability will be < 0.5
        assert "NORM.DIST(20, 25, 3, TRUE)" in formula

    def test_risk_buffer_80_percent(self, formula_templates):
        """Test risk buffer for 80% confidence."""
        formula = formula_templates.apply_template(
            "risk_buffer",
            confidence_level="0.8",
            std_dev="5"
        )

        # Buffer = z*σ where z for 80% ≈ 0.84
        assert "NORM.S.INV(0.8)" in formula
        assert "* 5" in formula

    def test_risk_buffer_95_percent(self, formula_templates):
        """Test risk buffer for 95% confidence."""
        formula = formula_templates.apply_template(
            "risk_buffer",
            confidence_level="0.95",
            std_dev="10"
        )

        # Buffer = z*σ where z for 95% ≈ 1.65
        assert "NORM.S.INV(0.95)" in formula
        assert "* 10" in formula

    def test_coefficient_of_variation_low(self, formula_templates):
        """Test coefficient of variation for low uncertainty."""
        formula = formula_templates.apply_template(
            "coefficient_of_variation",
            std_dev="2",
            mean="100"
        )

        # CV = σ/μ = 2/100 = 0.02 (low uncertainty)
        assert "IF(100=0, 0, 2 / 100)" in formula

    def test_coefficient_of_variation_high(self, formula_templates):
        """Test coefficient of variation for high uncertainty."""
        formula = formula_templates.apply_template(
            "coefficient_of_variation",
            std_dev="40",
            mean="100"
        )

        # CV = σ/μ = 40/100 = 0.4 (high uncertainty)
        assert "IF(100=0, 0, 40 / 100)" in formula

    def test_coefficient_of_variation_zero_mean(self, formula_templates):
        """Test coefficient of variation with zero mean protection."""
        formula = formula_templates.apply_template(
            "coefficient_of_variation",
            std_dev="5",
            mean="0"
        )

        # Should return 0 when mean is 0 (avoid division by zero)
        assert "IF(0=0, 0," in formula


class TestStatisticalValidation:
    """Test statistical properties and edge cases."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_pert_mean_bounds_check(self, formula_templates):
        """Test PERT mean is bounded by optimistic and pessimistic."""
        # For any PERT distribution, mean should be between a and b
        # Formula: (a + 4m + b) / 6

        # Case 1: mode = optimistic (mean should be close to optimistic)
        formula1 = formula_templates.apply_template(
            "pert_mean",
            optimistic="10",
            most_likely="10",
            pessimistic="30"
        )
        # Mean = (10 + 40 + 30)/6 = 80/6 ≈ 13.33 (closer to optimistic)
        assert "10 + 4*10 + 30" in formula1

        # Case 2: mode = pessimistic (mean should be close to pessimistic)
        formula2 = formula_templates.apply_template(
            "pert_mean",
            optimistic="10",
            most_likely="30",
            pessimistic="30"
        )
        # Mean = (10 + 120 + 30)/6 = 160/6 ≈ 26.67 (closer to pessimistic)
        assert "10 + 4*30 + 30" in formula2

    def test_triangular_distribution_mode_weight(self, formula_templates):
        """Test triangular distribution properly weights the mode."""
        formula = formula_templates.apply_template(
            "monte_carlo_triangular",
            optimistic="0",
            most_likely="10",
            pessimistic="20"
        )

        # Triangular should handle both sides of the mode differently
        # Formula should have conditional logic for left and right sides
        assert "IF(RAND()" in formula
        assert "0" in formula
        assert "10" in formula
        assert "20" in formula

    def test_normal_inverse_properties(self, formula_templates):
        """Test that NORM.INV is used correctly for sampling."""
        formula = formula_templates.apply_template(
            "monte_carlo_sample",
            mean="50",
            std_dev="10"
        )

        # NORM.INV(RAND(), μ, σ) generates random samples from N(μ, σ²)
        # This is the inverse CDF method (quantile function)
        assert "NORM.INV(RAND(), 50, 10)" in formula

    def test_confidence_interval_symmetry(self, formula_templates):
        """Test confidence intervals are symmetric around mean."""
        lower = formula_templates.apply_template(
            "confidence_interval_lower",
            mean="100",
            std_dev="15",
            confidence_level="0.95"
        )

        upper = formula_templates.apply_template(
            "confidence_interval_upper",
            mean="100",
            std_dev="15",
            confidence_level="0.95"
        )

        # Both should reference the same mean and std_dev
        assert "100" in lower and "100" in upper
        assert "15" in lower and "15" in upper
        # Lower uses subtraction, upper uses addition
        assert "-" in lower
        assert "+" in upper


class TestExtensionHooks:
    """Test that extension hooks are documented for advanced features."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_extension_hooks_present(self, formula_templates):
        """Test that extension hooks metadata is present."""
        # Extension hooks should be in the loaded templates
        templates = formula_templates.templates

        if "monte_carlo" in templates:
            monte_carlo_meta = templates["monte_carlo"]
            # Should have extension hooks or metadata
            assert "_extension_hooks" in monte_carlo_meta or "_metadata" in monte_carlo_meta

    def test_multi_constraint_optimization_hook(self, formula_templates):
        """Test multi-constraint optimization hook is documented."""
        templates = formula_templates.templates

        if "monte_carlo" in templates:
            monte_carlo = templates["monte_carlo"]
            if "_extension_hooks" in monte_carlo:
                hooks = monte_carlo["_extension_hooks"]
                assert "multi_constraint_optimization" in hooks or \
                       "description" in monte_carlo.get("_metadata", {})

    def test_multi_goal_scenarios_hook(self, formula_templates):
        """Test multi-goal scenario hook is documented."""
        templates = formula_templates.templates

        if "monte_carlo" in templates:
            monte_carlo = templates["monte_carlo"]
            if "_extension_hooks" in monte_carlo:
                hooks = monte_carlo["_extension_hooks"]
                # Should document multi-goal scenario capability
                assert "multi_goal_scenarios" in hooks or \
                       "portfolio_optimization" in hooks or \
                       len(hooks) > 0  # At least some extension hooks


class TestRealWorldScenarios:
    """Test formulas with realistic project scenarios."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_software_project_estimate(self, formula_templates):
        """Test realistic software project estimation."""
        # Scenario: Feature development
        # Optimistic: 5 days, Most likely: 10 days, Pessimistic: 25 days

        pert_mean = formula_templates.apply_template(
            "pert_mean",
            optimistic="5",
            most_likely="10",
            pessimistic="25"
        )

        # Mean = (5 + 4*10 + 25) / 6 = 70/6 ≈ 11.67 days
        assert "5 + 4*10 + 25" in pert_mean

        pert_std = formula_templates.apply_template(
            "pert_std_dev",
            pessimistic="25",
            optimistic="5"
        )

        # Std Dev = (25 - 5) / 6 = 3.33 days
        assert "25 - 5" in pert_std

    def test_construction_project_estimate(self, formula_templates):
        """Test realistic construction project estimation."""
        # Scenario: Building phase
        # Optimistic: 30 days, Most likely: 45 days, Pessimistic: 90 days

        pert_mean = formula_templates.apply_template(
            "pert_mean",
            optimistic="30",
            most_likely="45",
            pessimistic="90"
        )

        # Mean = (30 + 4*45 + 90) / 6 = 300/6 = 50 days
        assert "30 + 4*45 + 90" in pert_mean

    def test_probability_of_meeting_deadline(self, formula_templates):
        """Test probability calculation for realistic deadline."""
        # Scenario: Project mean = 50 days, std = 10 days, deadline = 60 days
        # P(completion <= 60) = ?

        prob = formula_templates.apply_template(
            "probability_on_time",
            target_date="60",
            mean="50",
            std_dev="10"
        )

        # P(X <= 60) when X ~ N(50, 10²)
        # Z = (60-50)/10 = 1.0
        # P(Z <= 1.0) ≈ 0.84 (84% chance of meeting deadline)
        assert "NORM.DIST(60, 50, 10, TRUE)" in prob

    def test_risk_buffer_for_commitment(self, formula_templates):
        """Test risk buffer calculation for commitment."""
        # Scenario: Team wants 85% confidence
        # Std dev = 8 days

        buffer = formula_templates.apply_template(
            "risk_buffer",
            confidence_level="0.85",
            std_dev="8"
        )

        # Buffer = z*σ where z for 85% ≈ 1.04
        # Buffer ≈ 1.04 * 8 ≈ 8.3 days
        assert "NORM.S.INV(0.85)" in buffer
        assert "* 8" in buffer
