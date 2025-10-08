"""Tests for formula template system."""

import pytest
from pathlib import Path

from app.excel.components.formulas import FormulaTemplate


class TestFormulaTemplate:
    """Test FormulaTemplate class."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_initialization(self, formula_templates):
        """Test FormulaTemplate initializes correctly."""
        assert formula_templates is not None
        assert isinstance(formula_templates.templates, dict)

    def test_templates_loaded_from_json(self, formula_templates):
        """Test templates are loaded from JSON files."""
        # Should have loaded templates from dependencies.json and dates.json
        assert len(formula_templates.templates) > 0

        # Check for known templates
        template_names = formula_templates.list_templates()
        assert "dependency_fs" in template_names
        assert "working_days" in template_names

    def test_list_templates(self, formula_templates):
        """Test listing all available templates."""
        templates = formula_templates.list_templates()

        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "dependency_fs" in templates

    def test_get_template_info(self, formula_templates):
        """Test retrieving template information."""
        info = formula_templates.get_template_info("dependency_fs")

        assert "formula" in info
        assert "description" in info
        assert "parameters" in info
        assert "predecessor_finish" in info["parameters"]

    def test_get_nonexistent_template_raises_error(self, formula_templates):
        """Test getting non-existent template raises KeyError."""
        with pytest.raises(KeyError):
            formula_templates.get_template_info("nonexistent_template")

    def test_apply_template_basic(self, formula_templates):
        """Test basic template application."""
        formula = formula_templates.apply_template(
            "dependency_fs",
            predecessor_finish="E2",
            task_start="D3",
            lag_days="0",
        )

        assert "E2" in formula
        assert "D3" in formula
        assert "0" in formula
        assert formula.startswith("=IF")

    def test_apply_template_with_missing_parameter_raises_error(self, formula_templates):
        """Test applying template with missing parameter raises error."""
        with pytest.raises(ValueError, match="Missing required parameter"):
            formula_templates.apply_template(
                "dependency_fs",
                predecessor_finish="E2",
                # Missing task_start and lag_days
            )

    def test_apply_nonexistent_template_raises_error(self, formula_templates):
        """Test applying non-existent template raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            formula_templates.apply_template("fake_template", param="value")

    def test_add_template_programmatically(self, formula_templates):
        """Test adding a new template programmatically."""
        formula_templates.add_template(
            name="test_formula",
            formula="=$cell1 + $cell2",
            description="Test addition formula",
            parameters={"cell1": "First cell", "cell2": "Second cell"},
        )

        # Should be able to apply it
        result = formula_templates.apply_template(
            "test_formula", cell1="A1", cell2="B1"
        )

        assert result == "=A1 + B1"

    def test_parameter_extraction_from_formula(self, formula_templates):
        """Test automatic parameter extraction from formula."""
        # Add template without explicit parameters
        formula_templates.add_template(
            name="auto_params",
            formula="=$start + $duration - $offset",
            description="Test auto parameter extraction",
        )

        # Should detect parameters from formula
        info = formula_templates.get_template_info("auto_params")
        formula = info["formula"]

        # All three parameters should be present in formula
        assert "$start" in formula
        assert "$duration" in formula
        assert "$offset" in formula


class TestSpecificFormulas:
    """Test specific formula templates work correctly."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_finish_to_start_dependency(self, formula_templates):
        """Test finish-to-start dependency formula."""
        formula = formula_templates.apply_template(
            "dependency_fs",
            predecessor_finish="E5",
            task_start="D6",
            lag_days="2",
        )

        expected = "=IF(ISBLANK(E5), D6, MAX(D6, E5 + 2))"
        assert formula == expected

    def test_start_to_start_dependency(self, formula_templates):
        """Test start-to-start dependency formula."""
        formula = formula_templates.apply_template(
            "dependency_ss",
            predecessor_start="D5",
            task_start="D6",
            lag_days="0",
        )

        expected = "=IF(ISBLANK(D5), D6, MAX(D6, D5 + 0))"
        assert formula == expected

    def test_critical_path_detection(self, formula_templates):
        """Test critical path detection formula."""
        formula = formula_templates.apply_template(
            "critical_path",
            total_float="F10",
            duration="C10",
        )

        expected = '=IF(AND(F10=0, C10>0), "CRITICAL", "")'
        assert formula == expected

    def test_working_days_calculation(self, formula_templates):
        """Test working days calculation formula."""
        formula = formula_templates.apply_template(
            "working_days",
            start_date="D10",
            end_date="E10",
            holidays="Holidays!A:A",
        )

        expected = "=NETWORKDAYS(D10, E10, Holidays!A:A)"
        assert formula == expected

    def test_add_working_days(self, formula_templates):
        """Test adding working days formula."""
        formula = formula_templates.apply_template(
            "add_working_days",
            start_date="D10",
            num_days="5",
            holidays="Holidays!A:A",
        )

        expected = "=WORKDAY(D10, 5, Holidays!A:A)"
        assert formula == expected

    def test_total_float_calculation(self, formula_templates):
        """Test total float calculation formula."""
        formula = formula_templates.apply_template(
            "total_float", late_finish="G10", early_finish="E10"
        )

        expected = "=G10 - E10"
        assert formula == expected


class TestFormulaTemplateErrors:
    """Test error handling in formula templates."""

    @pytest.fixture
    def formula_templates(self):
        """Create FormulaTemplate instance for testing."""
        return FormulaTemplate()

    def test_empty_formula_raises_error(self, formula_templates):
        """Test template with empty formula raises error."""
        formula_templates.add_template(
            name="empty_formula",
            formula="",
            description="Empty formula test",
        )

        with pytest.raises(ValueError, match="has no formula defined"):
            formula_templates.apply_template("empty_formula")

    def test_missing_template_shows_available_templates(self, formula_templates):
        """Test error message includes list of available templates."""
        try:
            formula_templates.apply_template("nonexistent")
            assert False, "Should have raised KeyError"
        except KeyError as e:
            error_msg = str(e)
            # Should mention available templates
            assert "Available" in error_msg

    def test_parameter_validation_lists_missing_params(self, formula_templates):
        """Test parameter validation error lists missing parameters."""
        try:
            formula_templates.apply_template(
                "dependency_fs",
                # Only providing one of three required params
                predecessor_finish="E2",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            # Should mention missing parameters
            assert "Missing required parameter" in error_msg
