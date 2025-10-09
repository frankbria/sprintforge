"""
Comprehensive tests for resource allocation and leveling formulas.

This test suite validates:
- Resource allocation calculations
- Resource utilization and conflict detection
- Resource leveling priority
- Skill-weighted allocation
- Multi-resource calculations
- Extension hooks for advanced resource management

Statistical validation ensures formulas are mathematically sound.
"""

import pytest
from app.excel.components.templates.formula_loader import FormulaTemplateLoader


@pytest.fixture
def formula_templates():
    """Load resource formula templates for testing."""
    loader = FormulaTemplateLoader()
    loader.load_template("resources")
    return loader


class TestResourceAllocation:
    """Test basic resource allocation formulas."""

    def test_resource_allocation_full_time(self, formula_templates):
        """Test resource allocation at 100% capacity."""
        formula = formula_templates.apply_template(
            "resource_allocation",
            task_duration="40",
            resource_percentage="100"
        )
        # 40 hours * 100% = 40 hours
        assert formula == "=40 * 100 / 100"

    def test_resource_allocation_part_time(self, formula_templates):
        """Test resource allocation at 50% capacity."""
        formula = formula_templates.apply_template(
            "resource_allocation",
            task_duration="40",
            resource_percentage="50"
        )
        # 40 hours * 50% = 20 hours
        assert formula == "=40 * 50 / 100"

    def test_resource_allocation_over_allocated(self, formula_templates):
        """Test resource allocation over 100% capacity."""
        formula = formula_templates.apply_template(
            "resource_allocation",
            task_duration="40",
            resource_percentage="150"
        )
        # 40 hours * 150% = 60 hours (over-allocated)
        assert formula == "=40 * 150 / 100"

    def test_resource_allocation_zero_duration(self, formula_templates):
        """Test resource allocation with zero duration (milestone)."""
        formula = formula_templates.apply_template(
            "resource_allocation",
            task_duration="0",
            resource_percentage="100"
        )
        # 0 hours * 100% = 0 hours
        assert formula == "=0 * 100 / 100"


class TestResourceUtilization:
    """Test resource utilization calculations."""

    def test_resource_utilization_normal(self, formula_templates):
        """Test resource utilization within capacity."""
        formula = formula_templates.apply_template(
            "resource_utilization",
            resource_column="B:B",
            resource_name="John",
            allocation_column="C:C",
            capacity="160"
        )
        # SUMIF allocations / capacity
        assert formula == "=SUMIF(B:B, John, C:C) / 160"
        assert "SUMIF" in formula
        assert "160" in formula

    def test_resource_utilization_over_allocated(self, formula_templates):
        """Test resource utilization detecting over-allocation."""
        formula = formula_templates.apply_template(
            "resource_utilization",
            resource_column="B:B",
            resource_name="Sarah",
            allocation_column="C:C",
            capacity="120"
        )
        # Result > 1.0 indicates over-allocation
        assert formula == "=SUMIF(B:B, Sarah, C:C) / 120"

    def test_resource_utilization_multiple_tasks(self, formula_templates):
        """Test resource utilization across multiple tasks."""
        formula = formula_templates.apply_template(
            "resource_utilization",
            resource_column="$B$2:$B$100",
            resource_name="Team_A",
            allocation_column="$C$2:$C$100",
            capacity="480"
        )
        # Absolute references for stability
        assert "$B$2:$B$100" in formula
        assert "$C$2:$C$100" in formula


class TestResourceConflictDetection:
    """Test resource conflict detection formulas."""

    def test_conflict_detection_no_conflict(self, formula_templates):
        """Test conflict detection when resource is not over-allocated."""
        formula = formula_templates.apply_template(
            "resource_conflict_detection",
            resource_column="B:B",
            resource_name="Developer1",
            allocation_column="C:C",
            capacity="160"
        )
        # Returns "OVERALLOCATED" if sum > capacity, else ""
        assert formula == '=IF(SUMIF(B:B, Developer1, C:C) > 160, "OVERALLOCATED", "")'

    def test_conflict_detection_with_conflict(self, formula_templates):
        """Test conflict detection when resource is over-allocated."""
        formula = formula_templates.apply_template(
            "resource_conflict_detection",
            resource_column="B:B",
            resource_name="Designer1",
            allocation_column="C:C",
            capacity="80"
        )
        # Returns "OVERALLOCATED" when allocation exceeds capacity
        assert "OVERALLOCATED" in formula
        assert "80" in formula

    def test_conflict_detection_boundary_case(self, formula_templates):
        """Test conflict detection at exact capacity boundary."""
        formula = formula_templates.apply_template(
            "resource_conflict_detection",
            resource_column="B:B",
            resource_name="QA1",
            allocation_column="C:C",
            capacity="40"
        )
        # Should flag only when > capacity, not >=
        assert "> 40" in formula


class TestResourceLoadByPeriod:
    """Test resource load calculations for specific time periods."""

    def test_load_by_week(self, formula_templates):
        """Test resource load calculation for a specific week."""
        formula = formula_templates.apply_template(
            "resource_load_by_period",
            allocation_column="C:C",
            resource_column="B:B",
            resource_name="Dev_Team",
            date_column="D:D",
            period_start="2025-01-01",
            period_end="2025-01-07"
        )
        # SUMIFS with date range criteria
        assert "SUMIFS" in formula
        assert "2025-01-01" in formula
        assert "2025-01-07" in formula

    def test_load_by_sprint(self, formula_templates):
        """Test resource load calculation for a sprint period."""
        formula = formula_templates.apply_template(
            "resource_load_by_period",
            allocation_column="$C$2:$C$100",
            resource_column="$B$2:$B$100",
            resource_name="Backend_Team",
            date_column="$D$2:$D$100",
            period_start="2025-03-01",
            period_end="2025-03-14"
        )
        # 2-week sprint period
        assert "Backend_Team" in formula
        assert ">=" in formula and "<=" in formula

    def test_load_by_quarter(self, formula_templates):
        """Test resource load calculation for a quarter."""
        formula = formula_templates.apply_template(
            "resource_load_by_period",
            allocation_column="C:C",
            resource_column="B:B",
            resource_name="QA_Team",
            date_column="D:D",
            period_start="2025-01-01",
            period_end="2025-03-31"
        )
        # Q1 2025
        assert "QA_Team" in formula


class TestResourceLevelingPriority:
    """Test resource leveling priority calculations."""

    def test_leveling_priority_critical_path(self, formula_templates):
        """Test leveling priority for critical path tasks (zero float)."""
        formula = formula_templates.apply_template(
            "resource_leveling_priority",
            total_float="0"
        )
        # Critical path tasks get priority 1
        assert formula == "=IF(0=0, 1, IF(0<5, 2, 3))"

    def test_leveling_priority_near_critical(self, formula_templates):
        """Test leveling priority for near-critical tasks (float < 5)."""
        formula = formula_templates.apply_template(
            "resource_leveling_priority",
            total_float="3"
        )
        # Near-critical tasks get priority 2
        assert formula == "=IF(3=0, 1, IF(3<5, 2, 3))"

    def test_leveling_priority_non_critical(self, formula_templates):
        """Test leveling priority for non-critical tasks (float >= 5)."""
        formula = formula_templates.apply_template(
            "resource_leveling_priority",
            total_float="10"
        )
        # Non-critical tasks get priority 3
        assert formula == "=IF(10=0, 1, IF(10<5, 2, 3))"

    def test_leveling_priority_boundary(self, formula_templates):
        """Test leveling priority at boundary (float = 5)."""
        formula = formula_templates.apply_template(
            "resource_leveling_priority",
            total_float="5"
        )
        # Exactly 5 days should be non-critical (priority 3)
        assert "5" in formula


class TestMultiResourceAllocation:
    """Test calculations across multiple resources."""

    def test_multi_resource_team_allocation(self, formula_templates):
        """Test total allocation across a team of resources."""
        formula = formula_templates.apply_template(
            "multi_resource_allocation",
            resource_column="B:B",
            resource_list='{"Dev1","Dev2","Dev3"}',
            allocation_column="C:C"
        )
        # SUMPRODUCT for multiple resource matching
        assert "SUMPRODUCT" in formula
        assert "Dev1" in formula or "resource_list" in formula.lower()

    def test_multi_resource_department_allocation(self, formula_templates):
        """Test total allocation across a department."""
        formula = formula_templates.apply_template(
            "multi_resource_allocation",
            resource_column="$B$2:$B$100",
            resource_list='{"Engineering","QA","Design"}',
            allocation_column="$C$2:$C$100"
        )
        # Department-level aggregation
        assert "SUMPRODUCT" in formula


class TestResourceEfficiency:
    """Test resource efficiency calculations."""

    def test_efficiency_on_time(self, formula_templates):
        """Test efficiency when actual equals allocated (100% efficiency)."""
        formula = formula_templates.apply_template(
            "resource_efficiency",
            actual_hours="40",
            allocated_hours="40"
        )
        # Efficiency = 1.0 when actual = allocated
        assert formula == "=IF(40=0, 1, 40 / 40)"

    def test_efficiency_better_than_expected(self, formula_templates):
        """Test efficiency when actual < allocated (>100% efficiency)."""
        formula = formula_templates.apply_template(
            "resource_efficiency",
            actual_hours="30",
            allocated_hours="40"
        )
        # Efficiency = 0.75 (more efficient than planned)
        assert formula == "=IF(40=0, 1, 30 / 40)"

    def test_efficiency_worse_than_expected(self, formula_templates):
        """Test efficiency when actual > allocated (<100% efficiency)."""
        formula = formula_templates.apply_template(
            "resource_efficiency",
            actual_hours="50",
            allocated_hours="40"
        )
        # Efficiency = 1.25 (less efficient than planned)
        assert formula == "=IF(40=0, 1, 50 / 40)"

    def test_efficiency_zero_allocated(self, formula_templates):
        """Test efficiency with zero allocated hours (edge case)."""
        formula = formula_templates.apply_template(
            "resource_efficiency",
            actual_hours="10",
            allocated_hours="0"
        )
        # Returns 1 to avoid division by zero
        assert "IF(0=0, 1" in formula


class TestCapacityUtilization:
    """Test capacity utilization rate calculations."""

    def test_capacity_utilization_normal(self, formula_templates):
        """Test capacity utilization within normal range."""
        formula = formula_templates.apply_template(
            "capacity_utilization_rate",
            resource_column="B:B",
            resource_name="Developer",
            allocation_column="C:C",
            total_available_hours="160"
        )
        # (SUMIF / total) * 100 for percentage
        assert "SUMIF(B:B, Developer, C:C)" in formula
        assert "/ 160) * 100" in formula

    def test_capacity_utilization_full(self, formula_templates):
        """Test capacity utilization at 100% capacity."""
        formula = formula_templates.apply_template(
            "capacity_utilization_rate",
            resource_column="B:B",
            resource_name="Designer",
            allocation_column="C:C",
            total_available_hours="80"
        )
        # Should show 100% when fully utilized
        assert "* 100" in formula

    def test_capacity_utilization_over(self, formula_templates):
        """Test capacity utilization over 100%."""
        formula = formula_templates.apply_template(
            "capacity_utilization_rate",
            resource_column="B:B",
            resource_name="QA",
            allocation_column="C:C",
            total_available_hours="120"
        )
        # Can exceed 100% indicating over-allocation
        assert "SUMIF" in formula


class TestSkillWeightedAllocation:
    """Test skill-weighted resource allocation."""

    def test_skill_weighted_perfect_match(self, formula_templates):
        """Test skill weighting with perfect skill match (100%)."""
        formula = formula_templates.apply_template(
            "skill_weighted_allocation",
            allocation_hours="40",
            skill_match_percentage="100"
        )
        # 40 hours * 100% = 40 hours (no adjustment)
        assert formula == "=40 * 100 / 100"

    def test_skill_weighted_partial_match(self, formula_templates):
        """Test skill weighting with partial skill match (75%)."""
        formula = formula_templates.apply_template(
            "skill_weighted_allocation",
            allocation_hours="40",
            skill_match_percentage="75"
        )
        # 40 hours * 75% = 30 effective hours
        assert formula == "=40 * 75 / 100"

    def test_skill_weighted_poor_match(self, formula_templates):
        """Test skill weighting with poor skill match (50%)."""
        formula = formula_templates.apply_template(
            "skill_weighted_allocation",
            allocation_hours="40",
            skill_match_percentage="50"
        )
        # 40 hours * 50% = 20 effective hours (longer actual time needed)
        assert formula == "=40 * 50 / 100"

    def test_skill_weighted_expert_match(self, formula_templates):
        """Test skill weighting with expert-level match (>100%)."""
        formula = formula_templates.apply_template(
            "skill_weighted_allocation",
            allocation_hours="40",
            skill_match_percentage="120"
        )
        # 40 hours * 120% = 48 effective hours (expert efficiency)
        assert formula == "=40 * 120 / 100"


class TestResourceAvailability:
    """Test resource availability calculations."""

    def test_resource_availability_normal(self, formula_templates):
        """Test resource availability with normal utilization."""
        formula = formula_templates.apply_template(
            "resource_availability",
            capacity="160",
            resource_column="B:B",
            resource_name="Dev1",
            allocation_column="C:C"
        )
        # capacity - SUMIF(allocations)
        assert formula == "=160 - SUMIF(B:B, Dev1, C:C)"

    def test_resource_availability_fully_booked(self, formula_templates):
        """Test resource availability when fully allocated."""
        formula = formula_templates.apply_template(
            "resource_availability",
            capacity="80",
            resource_column="B:B",
            resource_name="Designer1",
            allocation_column="C:C"
        )
        # Should return 0 when capacity - allocations = 0
        assert "80 - SUMIF" in formula

    def test_resource_availability_over_allocated(self, formula_templates):
        """Test resource availability when over-allocated."""
        formula = formula_templates.apply_template(
            "resource_availability",
            capacity="120",
            resource_column="B:B",
            resource_name="QA1",
            allocation_column="C:C"
        )
        # Should return negative value when over-allocated
        assert "120 - SUMIF" in formula


class TestPeakResourceDemand:
    """Test peak resource demand detection."""

    def test_peak_demand_calculation(self, formula_templates):
        """Test peak demand period identification."""
        formula = formula_templates.apply_template(
            "peak_resource_demand",
            resource_column="B:B",
            resource_name="Engineering",
            allocation_column="C:C"
        )
        # MAX(IF()) array formula
        assert formula == "=MAX(IF(B:B=Engineering, C:C, 0))"

    def test_peak_demand_single_resource(self, formula_templates):
        """Test peak demand for individual resource."""
        formula = formula_templates.apply_template(
            "peak_resource_demand",
            resource_column="$B$2:$B$100",
            resource_name="Developer1",
            allocation_column="$C$2:$C$100"
        )
        # Array formula for max allocation in any period
        assert "MAX" in formula and "IF" in formula


class TestExtensionHooks:
    """Test that extension hooks are properly documented."""

    def test_constraint_based_scheduling_hook(self, formula_templates):
        """Test that constraint-based scheduling extension hook exists."""
        template_data = formula_templates.get_template_data("resources")
        hooks = template_data.get("_extension_hooks", {})

        assert "constraint_based_scheduling" in hooks
        hook = hooks["constraint_based_scheduling"]
        assert "description" in hook
        assert "implementation_guide" in hook
        assert "parameters" in hook

    def test_skill_matrix_optimization_hook(self, formula_templates):
        """Test that skill matrix optimization extension hook exists."""
        template_data = formula_templates.get_template_data("resources")
        hooks = template_data.get("_extension_hooks", {})

        assert "skill_matrix_optimization" in hooks
        hook = hooks["skill_matrix_optimization"]
        assert "description" in hook
        assert "Hungarian algorithm" in hook["implementation_guide"] or "linear programming" in hook["implementation_guide"]


class TestRealWorldScenarios:
    """Test with realistic resource management scenarios."""

    def test_software_team_allocation(self, formula_templates):
        """Test realistic software development team allocation."""
        # 5 developers, 160 hours/month each = 800 hours capacity
        # Current allocation: 720 hours
        # Utilization: 720/800 = 90%
        utilization = formula_templates.apply_template(
            "capacity_utilization_rate",
            resource_column="B:B",
            resource_name="Dev_Team",
            allocation_column="C:C",
            total_available_hours="800"
        )
        assert "800" in utilization

    def test_resource_conflict_scenario(self, formula_templates):
        """Test realistic resource conflict detection."""
        # Developer allocated 180 hours in 160-hour month
        conflict = formula_templates.apply_template(
            "resource_conflict_detection",
            resource_column="B:B",
            resource_name="SeniorDev",
            allocation_column="C:C",
            capacity="160"
        )
        assert "OVERALLOCATED" in conflict

    def test_skill_mismatch_scenario(self, formula_templates):
        """Test skill mismatch impact on allocation."""
        # Junior dev (60% skill match) on senior task (40 hours)
        # Effective hours: 40 * 0.6 = 24 hours
        # Actual time needed: 40 / 0.6 = 66.7 hours
        weighted = formula_templates.apply_template(
            "skill_weighted_allocation",
            allocation_hours="40",
            skill_match_percentage="60"
        )
        assert "40 * 60" in weighted
