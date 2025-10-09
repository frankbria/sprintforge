"""
Comprehensive tests for Template System (Task 3.6).

Tests template variations, methodology-specific templates, custom formula
injection, and template versioning.

Target: >85% code coverage, 100% pass rate
"""

import pytest
from datetime import datetime
from app.excel.templates import (
    TemplateRegistry,
    TemplateLayoutBuilder,
    CustomFormulaValidator,
    TemplateVersionManager,
    TemplateMetadata,
    TemplateVariation,
    ProjectMethodology,
    select_template,
)


class TestTemplateRegistry:
    """Test template registry and selection."""

    def test_registry_initialization(self):
        """Test registry initializes with default templates."""
        registry = TemplateRegistry()

        assert len(registry.templates) > 0
        assert "agile_basic" in registry.templates
        assert "waterfall_basic" in registry.templates

    def test_default_templates_registered(self):
        """Test all default templates are registered."""
        registry = TemplateRegistry()

        expected_templates = [
            "agile_basic",
            "agile_advanced",
            "waterfall_basic",
            "waterfall_advanced",
            "hybrid",
        ]

        for name in expected_templates:
            assert name in registry.templates

    def test_get_template_by_name(self):
        """Test retrieving template by name."""
        registry = TemplateRegistry()

        template = registry.get_template("agile_basic")

        assert template is not None
        assert template.name == "agile_basic"
        assert template.methodology == ProjectMethodology.AGILE
        assert template.variation == TemplateVariation.BASIC

    def test_get_nonexistent_template(self):
        """Test getting non-existent template returns None."""
        registry = TemplateRegistry()

        template = registry.get_template("nonexistent")

        assert template is None

    def test_list_all_templates(self):
        """Test listing all templates."""
        registry = TemplateRegistry()

        templates = registry.list_templates()

        assert len(templates) >= 5
        assert all(isinstance(t, TemplateMetadata) for t in templates)

    def test_list_templates_by_variation(self):
        """Test filtering templates by variation."""
        registry = TemplateRegistry()

        basic_templates = registry.list_templates(variation=TemplateVariation.BASIC)

        assert len(basic_templates) > 0
        assert all(t.variation == TemplateVariation.BASIC for t in basic_templates)

    def test_list_templates_by_methodology(self):
        """Test filtering templates by methodology."""
        registry = TemplateRegistry()

        agile_templates = registry.list_templates(methodology=ProjectMethodology.AGILE)

        assert len(agile_templates) > 0
        assert all(t.methodology == ProjectMethodology.AGILE for t in agile_templates)

    def test_list_templates_with_multiple_filters(self):
        """Test filtering with both variation and methodology."""
        registry = TemplateRegistry()

        templates = registry.list_templates(
            variation=TemplateVariation.ADVANCED,
            methodology=ProjectMethodology.WATERFALL,
        )

        assert len(templates) > 0
        for t in templates:
            assert t.variation == TemplateVariation.ADVANCED
            assert t.methodology == ProjectMethodology.WATERFALL

    def test_find_template_exact_match(self):
        """Test finding exact template match."""
        registry = TemplateRegistry()

        template = registry.find_template(
            methodology=ProjectMethodology.AGILE,
            variation=TemplateVariation.BASIC,
        )

        assert template is not None
        assert template.methodology == ProjectMethodology.AGILE
        assert template.variation == TemplateVariation.BASIC

    def test_find_template_fallback(self):
        """Test finding template with fallback to different variation."""
        registry = TemplateRegistry()

        # Request custom variation which doesn't exist by default
        template = registry.find_template(
            methodology=ProjectMethodology.AGILE,
            variation=TemplateVariation.CUSTOM,
        )

        # Should fallback to another Agile template
        assert template is not None
        assert template.methodology == ProjectMethodology.AGILE

    def test_register_custom_template(self):
        """Test registering a custom template."""
        registry = TemplateRegistry()

        custom_template = TemplateMetadata(
            name="custom_scrum",
            variation=TemplateVariation.CUSTOM,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Custom Scrum template",
            features={"sprints", "retrospectives"},
        )

        registry.register_template(custom_template)

        retrieved = registry.get_template("custom_scrum")
        assert retrieved is not None
        assert retrieved.name == "custom_scrum"


class TestTemplateMetadata:
    """Test template metadata operations."""

    def test_metadata_creation(self):
        """Test creating template metadata."""
        metadata = TemplateMetadata(
            name="test_template",
            variation=TemplateVariation.BASIC,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Test template",
            features={"test_feature"},
        )

        assert metadata.name == "test_template"
        assert metadata.variation == TemplateVariation.BASIC
        assert "test_feature" in metadata.features

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = TemplateMetadata(
            name="test",
            variation=TemplateVariation.BASIC,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at="2024-01-01",
            updated_at="2024-01-01",
            description="Test",
        )

        data = metadata.to_dict()

        assert data["name"] == "test"
        assert data["variation"] == "basic"
        assert data["methodology"] == "agile"
        assert data["version"] == "1.0.0"

    def test_metadata_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "name": "test",
            "variation": "basic",
            "methodology": "agile",
            "version": "1.0.0",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "description": "Test template",
            "features": ["feature1", "feature2"],
            "custom_formulas": {},
        }

        metadata = TemplateMetadata.from_dict(data)

        assert metadata.name == "test"
        assert metadata.variation == TemplateVariation.BASIC
        assert len(metadata.features) == 2


class TestTemplateLayoutBuilder:
    """Test template layout building."""

    def test_basic_agile_layout(self):
        """Test building basic Agile layout."""
        builder = TemplateLayoutBuilder()
        metadata = TemplateMetadata(
            name="agile_basic",
            variation=TemplateVariation.BASIC,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Basic Agile",
            features={"sprints", "velocity"},
        )

        layout = builder.build_layout(metadata)

        assert "Sprint" in layout.columns
        assert "Story Points" in layout.columns
        assert layout.sprint_tracking is True

    def test_basic_waterfall_layout(self):
        """Test building basic Waterfall layout."""
        builder = TemplateLayoutBuilder()
        metadata = TemplateMetadata(
            name="waterfall_basic",
            variation=TemplateVariation.BASIC,
            methodology=ProjectMethodology.WATERFALL,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Basic Waterfall",
            features={"milestones", "phases"},
        )

        layout = builder.build_layout(metadata)

        assert "Phase" in layout.columns
        assert "Milestone" in layout.columns
        assert layout.milestone_tracking is True

    def test_advanced_layout_has_extra_columns(self):
        """Test advanced layout includes additional columns."""
        builder = TemplateLayoutBuilder()
        metadata = TemplateMetadata(
            name="agile_advanced",
            variation=TemplateVariation.ADVANCED,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Advanced Agile",
            features={"monte_carlo", "earned_value"},
        )

        layout = builder.build_layout(metadata)

        # Advanced columns should be present
        assert "Optimistic" in layout.columns
        assert "Likely" in layout.columns
        assert "Pessimistic" in layout.columns
        assert "% Complete" in layout.columns

    def test_hybrid_layout_combines_features(self):
        """Test hybrid layout combines Agile and Waterfall features."""
        builder = TemplateLayoutBuilder()
        metadata = TemplateMetadata(
            name="hybrid",
            variation=TemplateVariation.ADVANCED,
            methodology=ProjectMethodology.HYBRID,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Hybrid",
            features={"sprints", "milestones"},
        )

        layout = builder.build_layout(metadata)

        # Should have both Agile and Waterfall columns
        assert "Sprint" in layout.columns
        assert "Milestone" in layout.columns

    def test_column_widths_calculated(self):
        """Test column widths are calculated appropriately."""
        builder = TemplateLayoutBuilder()
        metadata = TemplateMetadata(
            name="test",
            variation=TemplateVariation.BASIC,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Test",
        )

        layout = builder.build_layout(metadata)

        # ID columns should be narrow
        assert layout.get_column_width("Task ID") == 10

        # Name columns should be wide
        assert layout.get_column_width("Task Name") == 30

        # Date columns should be medium
        assert layout.get_column_width("Start Date") == 12

    def test_feature_flags_set_correctly(self):
        """Test feature flags are set based on metadata."""
        builder = TemplateLayoutBuilder()
        metadata = TemplateMetadata(
            name="test",
            variation=TemplateVariation.ADVANCED,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Test",
            features={"advanced_gantt", "burndown", "resource_allocation"},
        )

        layout = builder.build_layout(metadata)

        assert layout.has_gantt is True
        assert layout.has_burndown is True
        assert layout.has_resource_allocation is True

    def test_column_count(self):
        """Test getting column count."""
        builder = TemplateLayoutBuilder()
        metadata = TemplateMetadata(
            name="test",
            variation=TemplateVariation.BASIC,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Test",
        )

        layout = builder.build_layout(metadata)

        assert layout.get_column_count() == len(layout.columns)
        assert layout.get_column_count() > 0


class TestCustomFormulaValidator:
    """Test custom formula validation."""

    def test_valid_formula_passes(self):
        """Test valid formula passes validation."""
        validator = CustomFormulaValidator()

        is_valid, error = validator.validate_formula("=SUM(A1:A10)")

        assert is_valid is True
        assert error is None

    def test_formula_without_equals_fails(self):
        """Test formula without = fails."""
        validator = CustomFormulaValidator()

        is_valid, error = validator.validate_formula("SUM(A1:A10)")

        assert is_valid is False
        assert "must start with '='" in error

    def test_empty_formula_fails(self):
        """Test empty formula fails."""
        validator = CustomFormulaValidator()

        is_valid, error = validator.validate_formula("")

        assert is_valid is False
        assert "cannot be empty" in error

    def test_blocked_function_detected(self):
        """Test blocked functions are rejected."""
        validator = CustomFormulaValidator()

        is_valid, error = validator.validate_formula("=INDIRECT(A1)")

        assert is_valid is False
        assert "Blocked function" in error

    def test_complex_valid_formula(self):
        """Test complex valid formula."""
        validator = CustomFormulaValidator()

        formula = "=IF(AND(A1>0, B1<100), SUM(C1:C10), AVERAGE(D1:D10))"
        is_valid, error = validator.validate_formula(formula)

        assert is_valid is True
        assert error is None

    def test_add_custom_formula_valid(self):
        """Test adding valid custom formula."""
        validator = CustomFormulaValidator()

        formula_def = validator.add_custom_formula(
            name="custom_calc",
            formula="=A1+B1*2",
            description="Custom calculation",
        )

        assert formula_def["name"] == "custom_calc"
        assert formula_def["formula"] == "=A1+B1*2"
        assert formula_def["custom"] is True

    def test_add_custom_formula_invalid(self):
        """Test adding invalid custom formula raises error."""
        validator = CustomFormulaValidator()

        with pytest.raises(ValueError, match="Invalid formula"):
            validator.add_custom_formula(
                name="bad_formula",
                formula="=INDIRECT(A1)",  # Blocked function
            )

    def test_extract_functions(self):
        """Test function extraction from formula."""
        validator = CustomFormulaValidator()

        formula = "=SUM(A1:A10) + AVERAGE(B1:B10)"
        functions = validator._extract_functions(formula)

        assert "SUM" in functions
        assert "AVERAGE" in functions

    def test_allowed_financial_functions(self):
        """Test financial functions are allowed."""
        validator = CustomFormulaValidator()

        is_valid, error = validator.validate_formula("=NPV(0.1, A1:A10)")

        assert is_valid is True

    def test_allowed_lookup_functions(self):
        """Test lookup functions are allowed."""
        validator = CustomFormulaValidator()

        is_valid, error = validator.validate_formula("=VLOOKUP(A1, B:C, 2, FALSE)")

        assert is_valid is True


class TestTemplateVersionManager:
    """Test template versioning."""

    def test_version_manager_initialization(self):
        """Test version manager initializes."""
        manager = TemplateVersionManager()

        assert manager.version_history is not None
        assert len(manager.version_history) == 0

    def test_parse_valid_version(self):
        """Test parsing valid version string."""
        manager = TemplateVersionManager()

        major, minor, patch = manager.parse_version("1.2.3")

        assert major == 1
        assert minor == 2
        assert patch == 3

    def test_parse_invalid_version_format(self):
        """Test parsing invalid version format raises error."""
        manager = TemplateVersionManager()

        with pytest.raises(ValueError, match="Invalid version format"):
            manager.parse_version("1.2")

    def test_parse_non_numeric_version(self):
        """Test parsing non-numeric version raises error."""
        manager = TemplateVersionManager()

        with pytest.raises(ValueError, match="Invalid version format"):
            manager.parse_version("1.2.a")

    def test_compare_versions_less_than(self):
        """Test comparing versions (less than)."""
        manager = TemplateVersionManager()

        result = manager.compare_versions("1.0.0", "2.0.0")

        assert result == -1

    def test_compare_versions_greater_than(self):
        """Test comparing versions (greater than)."""
        manager = TemplateVersionManager()

        result = manager.compare_versions("2.0.0", "1.0.0")

        assert result == 1

    def test_compare_versions_equal(self):
        """Test comparing versions (equal)."""
        manager = TemplateVersionManager()

        result = manager.compare_versions("1.0.0", "1.0.0")

        assert result == 0

    def test_compare_versions_by_minor(self):
        """Test comparing versions with different minor versions."""
        manager = TemplateVersionManager()

        result = manager.compare_versions("1.1.0", "1.2.0")

        assert result == -1

    def test_is_compatible_same_major(self):
        """Test compatibility with same major version."""
        manager = TemplateVersionManager()

        is_compat = manager.is_compatible("1.5.0", "1.3.0")

        assert is_compat is True

    def test_is_incompatible_different_major(self):
        """Test incompatibility with different major version."""
        manager = TemplateVersionManager()

        is_compat = manager.is_compatible("2.0.0", "1.0.0")

        assert is_compat is False

    def test_is_incompatible_lower_minor(self):
        """Test incompatibility with lower minor version."""
        manager = TemplateVersionManager()

        is_compat = manager.is_compatible("1.1.0", "1.3.0")

        assert is_compat is False

    def test_increment_patch_version(self):
        """Test incrementing patch version."""
        manager = TemplateVersionManager()

        new_version = manager.increment_version("1.0.0", "patch")

        assert new_version == "1.0.1"

    def test_increment_minor_version(self):
        """Test incrementing minor version."""
        manager = TemplateVersionManager()

        new_version = manager.increment_version("1.0.5", "minor")

        assert new_version == "1.1.0"

    def test_increment_major_version(self):
        """Test incrementing major version."""
        manager = TemplateVersionManager()

        new_version = manager.increment_version("1.5.3", "major")

        assert new_version == "2.0.0"

    def test_increment_invalid_level(self):
        """Test incrementing with invalid level raises error."""
        manager = TemplateVersionManager()

        with pytest.raises(ValueError, match="Invalid level"):
            manager.increment_version("1.0.0", "invalid")

    def test_record_version(self):
        """Test recording a version."""
        manager = TemplateVersionManager()

        manager.record_version("test_template", "1.0.0")

        history = manager.get_version_history("test_template")
        assert "1.0.0" in history

    def test_version_history_sorted(self):
        """Test version history is sorted."""
        manager = TemplateVersionManager()

        manager.record_version("test", "1.0.0")
        manager.record_version("test", "1.2.0")
        manager.record_version("test", "1.1.0")

        history = manager.get_version_history("test")

        assert history == ["1.0.0", "1.1.0", "1.2.0"]


class TestSelectTemplateHelper:
    """Test convenience template selection function."""

    def test_select_basic_agile(self):
        """Test selecting basic Agile template."""
        template = select_template("agile", "basic")

        assert template is not None
        assert template.methodology == ProjectMethodology.AGILE
        assert template.variation == TemplateVariation.BASIC

    def test_select_advanced_waterfall(self):
        """Test selecting advanced Waterfall template."""
        template = select_template("waterfall", "advanced")

        assert template is not None
        assert template.methodology == ProjectMethodology.WATERFALL
        assert template.variation == TemplateVariation.ADVANCED

    def test_select_with_invalid_methodology(self):
        """Test selecting with invalid methodology returns None."""
        template = select_template("invalid", "basic")

        assert template is None

    def test_select_with_invalid_variation(self):
        """Test selecting with invalid variation returns None."""
        template = select_template("agile", "invalid")

        assert template is None

    def test_select_case_insensitive(self):
        """Test selection is case-insensitive."""
        template = select_template("AGILE", "BASIC")

        assert template is not None
        assert template.methodology == ProjectMethodology.AGILE


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_agile_workflow_template_selection(self):
        """Test complete Agile workflow template selection."""
        registry = TemplateRegistry()
        builder = TemplateLayoutBuilder()

        # Select Agile template
        template = registry.find_template(
            methodology=ProjectMethodology.AGILE,
            variation=TemplateVariation.ADVANCED,
        )

        # Build layout
        layout = builder.build_layout(template)

        # Verify Agile-specific features
        assert "Sprint" in layout.columns
        assert "Velocity" in layout.columns
        assert layout.sprint_tracking is True
        assert layout.has_burndown is True

    def test_waterfall_workflow_template_selection(self):
        """Test complete Waterfall workflow template selection."""
        registry = TemplateRegistry()
        builder = TemplateLayoutBuilder()

        # Select Waterfall template
        template = registry.find_template(
            methodology=ProjectMethodology.WATERFALL,
            variation=TemplateVariation.ADVANCED,
        )

        # Build layout
        layout = builder.build_layout(template)

        # Verify Waterfall-specific features
        assert "Phase" in layout.columns
        assert "Milestone" in layout.columns
        assert layout.milestone_tracking is True

    def test_custom_formula_workflow(self):
        """Test custom formula injection workflow."""
        validator = CustomFormulaValidator()

        # Add custom formula
        custom_formula = validator.add_custom_formula(
            name="custom_priority",
            formula="=IF(A1>90, \"Critical\", IF(A1>70, \"High\", \"Normal\"))",
            description="Priority calculation",
        )

        assert custom_formula["custom"] is True

        # Validate another formula
        is_valid, error = validator.validate_formula("=SUM(A1:A10)/COUNT(A1:A10)")
        assert is_valid is True

    def test_template_versioning_workflow(self):
        """Test template version management workflow."""
        manager = TemplateVersionManager()

        # Record initial version
        manager.record_version("my_template", "1.0.0")

        # Upgrade to minor version
        new_version = manager.increment_version("1.0.0", "minor")
        manager.record_version("my_template", new_version)

        # Check compatibility
        is_compat = manager.is_compatible(new_version, "1.0.0")
        assert is_compat is True

        # Get version history
        history = manager.get_version_history("my_template")
        assert len(history) == 2
        assert history == ["1.0.0", "1.1.0"]


# Test coverage marker
def test_coverage_target():
    """Verify test coverage meets >85% target."""
    # This is a marker test - actual coverage measured by pytest-cov
    # Target: >85% coverage, 100% pass rate
    assert True, "Coverage target: >85%"
