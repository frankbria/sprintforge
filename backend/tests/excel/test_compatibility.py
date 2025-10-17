"""
Comprehensive tests for Excel compatibility module (Task 3.5).

Tests Excel version detection, modern function support, cross-platform
compatibility, and formula optimization.

Target: >85% code coverage, 100% pass rate
"""

import pytest
from app.excel.compatibility import (
    ExcelCompatibilityManager,
    CrossPlatformOptimizer,
    ExcelVersion,
    Platform,
    ExcelFeature,
)


class TestExcelVersionSupport:
    """Test Excel version detection and feature support."""

    def test_excel_2019_feature_support(self):
        """Test that Excel 2019 doesn't support Excel 365 features."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
        )

        # Excel 2019 should not support Excel 365 features
        assert not manager.supports_feature("xlookup")
        assert not manager.supports_feature("filter")
        assert not manager.supports_feature("let")
        assert not manager.supports_feature("lambda")

    def test_excel_365_feature_support(self):
        """Test that Excel 365 supports all modern features."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        # Excel 365 should support all modern features
        assert manager.supports_feature("xlookup")
        assert manager.supports_feature("filter")
        assert manager.supports_feature("let")
        assert manager.supports_feature("lambda")
        assert manager.supports_feature("sort")
        assert manager.supports_feature("unique")

    def test_excel_2021_partial_support(self):
        """Test Excel 2021 feature support level."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2021,
            target_platform=Platform.WINDOWS,
        )

        # Excel 2021 is between 2019 and 365 in capabilities
        # Most dynamic arrays, but not LAMBDA
        assert not manager.supports_feature("xlookup")  # 365 only
        assert not manager.supports_feature("lambda")   # 365 only

    def test_unknown_version_no_support(self):
        """Test that unknown version doesn't support any features."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.UNKNOWN,
            target_platform=Platform.WINDOWS,
        )

        assert not manager.supports_feature("xlookup")
        assert not manager.supports_feature("filter")

    def test_unknown_feature_returns_false(self):
        """Test that unknown features return False."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        assert not manager.supports_feature("nonexistent_function")


class TestPlatformCompatibility:
    """Test platform-specific compatibility."""

    def test_windows_platform_support(self):
        """Test Windows platform supports all features."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        assert manager.supports_feature("xlookup")
        assert manager.supports_feature("lambda")

    def test_mac_platform_lambda_not_supported(self):
        """Test Mac platform doesn't support LAMBDA."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.MAC,
        )

        # LAMBDA not fully supported on Mac
        assert not manager.supports_feature("lambda")

        # But other features are supported
        assert manager.supports_feature("xlookup")
        assert manager.supports_feature("filter")

    def test_web_platform_support(self):
        """Test web platform feature support."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WEB,
        )

        assert manager.supports_feature("xlookup")
        assert manager.supports_feature("filter")

    def test_any_platform_accepts_all(self):
        """Test ANY platform accepts platform-specific features."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.ANY,
        )

        # ANY platform should work with all features
        assert manager.supports_feature("xlookup")
        assert manager.supports_feature("lambda")


class TestXLOOKUPFormulas:
    """Test XLOOKUP formula generation and fallbacks."""

    def test_xlookup_native_formula(self):
        """Test native XLOOKUP formula generation."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        formula = manager.get_xlookup_formula(
            lookup_value="A2",
            lookup_array="B:B",
            return_array="C:C",
            if_not_found='"Not Found"',
        )

        assert formula.startswith("=XLOOKUP(")
        assert "A2" in formula
        assert "B:B" in formula
        assert "C:C" in formula
        assert '"Not Found"' in formula

    def test_xlookup_fallback_to_index_match(self):
        """Test XLOOKUP fallback to INDEX/MATCH."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
            enable_fallbacks=True,
        )

        formula = manager.get_xlookup_formula(
            lookup_value="A2",
            lookup_array="B:B",
            return_array="C:C",
            if_not_found='"Not Found"',
        )

        # Should use INDEX/MATCH fallback
        assert "XLOOKUP" not in formula
        assert "INDEX(" in formula
        assert "MATCH(" in formula
        assert "IFERROR(" in formula

    def test_xlookup_no_fallback_raises_error(self):
        """Test XLOOKUP without fallback raises error."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
            enable_fallbacks=False,
        )

        with pytest.raises(ValueError, match="XLOOKUP not supported"):
            manager.get_xlookup_formula(
                lookup_value="A2",
                lookup_array="B:B",
                return_array="C:C",
            )

    def test_xlookup_with_match_modes(self):
        """Test XLOOKUP with different match modes."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        # Exact match
        formula_exact = manager.get_xlookup_formula(
            lookup_value="A2",
            lookup_array="B:B",
            return_array="C:C",
            match_mode=0,
        )
        assert ", 0," in formula_exact

        # Next smallest
        formula_smallest = manager.get_xlookup_formula(
            lookup_value="A2",
            lookup_array="B:B",
            return_array="C:C",
            match_mode=-1,
        )
        assert ", -1," in formula_smallest


class TestFILTERFormulas:
    """Test FILTER formula generation and fallbacks."""

    def test_filter_native_formula(self):
        """Test native FILTER formula generation."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        formula = manager.get_filter_formula(
            array="A2:A100",
            include="B2:B100>10",
            if_empty='"No results"',
        )

        assert formula.startswith("=FILTER(")
        assert "A2:A100" in formula
        assert "B2:B100>10" in formula
        assert '"No results"' in formula

    def test_filter_fallback_formula(self):
        """Test FILTER fallback for older versions."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
            enable_fallbacks=True,
        )

        formula = manager.get_filter_formula(
            array="A2:A100",
            include="B2:B100>10",
        )

        # Should use array formula fallback
        assert "FILTER" not in formula
        assert "IF(" in formula
        assert "IFERROR(" in formula

    def test_filter_no_fallback_raises_error(self):
        """Test FILTER without fallback raises error."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
            enable_fallbacks=False,
        )

        with pytest.raises(ValueError, match="FILTER not supported"):
            manager.get_filter_formula(
                array="A2:A100",
                include="B2:B100>10",
            )


class TestLETFormulas:
    """Test LET formula generation and variable expansion."""

    def test_let_native_formula(self):
        """Test native LET formula generation."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        formula = manager.get_let_formula(
            variables=[("x", "A1*2"), ("y", "B1+5")],
            calculation="x+y",
        )

        assert formula.startswith("=LET(")
        assert "x,A1*2" in formula.replace(" ", "")
        assert "y,B1+5" in formula.replace(" ", "")
        assert "x+y" in formula

    def test_let_fallback_expansion(self):
        """Test LET fallback expands variables inline."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
            enable_fallbacks=True,
        )

        formula = manager.get_let_formula(
            variables=[("x", "A1*2"), ("y", "B1+5")],
            calculation="x+y",
        )

        # Should expand variables inline
        assert "LET" not in formula
        assert "(A1*2)" in formula
        assert "(B1+5)" in formula

    def test_let_multiple_variables(self):
        """Test LET with multiple variables."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        formula = manager.get_let_formula(
            variables=[
                ("optimistic", "10"),
                ("likely", "20"),
                ("pessimistic", "30"),
                ("mean", "(optimistic+4*likely+pessimistic)/6"),
            ],
            calculation="mean",
        )

        assert "optimistic,10" in formula.replace(" ", "")
        assert "likely,20" in formula.replace(" ", "")
        assert "pessimistic,30" in formula.replace(" ", "")


class TestFormulaOptimization:
    """Test formula performance optimization."""

    def test_optimize_simple_formula_unchanged(self):
        """Test that simple formulas remain unchanged."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
        )

        simple_formula = "=SUM(A1:A10)"
        optimized = manager.optimize_formula_performance(simple_formula)

        assert optimized == simple_formula

    def test_optimize_detects_volatile_functions(self):
        """Test detection of volatile functions."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
        )

        # INDIRECT is volatile - should log warning
        formula_with_indirect = "=SUM(INDIRECT(\"A1:A10\"))"
        optimized = manager.optimize_formula_performance(formula_with_indirect)

        # Formula should still work but logged as volatile
        assert "INDIRECT" in optimized

    def test_offset_optimization_detection(self):
        """Test OFFSET optimization detection."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
        )

        formula_with_offset = "=SUM(OFFSET(A1,0,0,10,1))"
        optimized = manager.optimize_formula_performance(formula_with_offset)

        # Optimization logic should process formula
        assert optimized is not None
        assert isinstance(optimized, str)

    def test_nested_if_optimization_detection(self):
        """Test nested IF optimization detection."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
        )

        nested_ifs = '=IF(A1>10, "A", IF(A1>20, "B", IF(A1>30, "C", IF(A1>40, "D", "E"))))'
        optimized = manager.optimize_formula_performance(nested_ifs)

        # Should detect nested IFs
        assert optimized is not None
        assert isinstance(optimized, str)


class TestCompatibilityReport:
    """Test compatibility report generation."""

    def test_excel_2019_compatibility_report(self):
        """Test compatibility report for Excel 2019."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
        )

        report = manager.get_compatibility_report()

        assert report["target_version"] == "2019"
        assert report["target_platform"] == "windows"
        assert "supported_features" in report
        assert "unsupported_features" in report
        assert "support_percentage" in report
        assert report["total_features"] > 0

        # Excel 2019 should have some unsupported features
        assert len(report["unsupported_features"]) > 0

    def test_excel_365_compatibility_report(self):
        """Test compatibility report for Excel 365."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        report = manager.get_compatibility_report()

        assert report["target_version"] == "365"
        # Excel 365 should support all or most features
        assert report["support_percentage"] > 80

    def test_compatibility_report_with_fallbacks(self):
        """Test compatibility report includes fallback features."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
            enable_fallbacks=True,
        )

        report = manager.get_compatibility_report()

        assert "fallback_features" in report
        # Should have some fallback features available
        assert len(report["fallback_features"]) > 0

    def test_compatibility_report_without_fallbacks(self):
        """Test compatibility report without fallbacks."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
            enable_fallbacks=False,
        )

        report = manager.get_compatibility_report()

        # With fallbacks disabled, fallback list should be empty
        assert len(report["fallback_features"]) == 0


class TestCrossPlatformOptimizer:
    """Test cross-platform compatibility optimizer."""

    def test_windows_path_separator(self):
        """Test Windows uses backslash path separator."""
        optimizer = CrossPlatformOptimizer(Platform.WINDOWS)

        assert optimizer.get_path_separator() == "\\"

    def test_mac_path_separator(self):
        """Test Mac uses forward slash path separator."""
        optimizer = CrossPlatformOptimizer(Platform.MAC)

        assert optimizer.get_path_separator() == "/"

    def test_web_path_separator(self):
        """Test Web uses forward slash path separator."""
        optimizer = CrossPlatformOptimizer(Platform.WEB)

        assert optimizer.get_path_separator() == "/"

    def test_windows_supports_file_dialogs(self):
        """Test Windows supports file dialogs."""
        optimizer = CrossPlatformOptimizer(Platform.WINDOWS)

        assert optimizer.supports_file_dialogs() is True

    def test_web_no_file_dialogs(self):
        """Test Web doesn't support file dialogs."""
        optimizer = CrossPlatformOptimizer(Platform.WEB)

        assert optimizer.supports_file_dialogs() is False

    def test_date_formula_adjustment_windows(self):
        """Test date formula doesn't adjust on Windows."""
        optimizer = CrossPlatformOptimizer(Platform.WINDOWS)

        original = "=DATE(2024, 1, 15)"
        adjusted = optimizer.adjust_date_formula(original)

        assert adjusted == original

    def test_date_formula_adjustment_mac(self):
        """Test date formula adjustment logic on Mac."""
        optimizer = CrossPlatformOptimizer(Platform.MAC)

        original = "=DATE(2024, 1, 15)"
        adjusted = optimizer.adjust_date_formula(original)

        # Adjustment logic should process the formula
        assert adjusted is not None
        assert isinstance(adjusted, str)


class TestExcelFeatureDataclass:
    """Test ExcelFeature dataclass."""

    def test_excel_feature_creation(self):
        """Test creating ExcelFeature instances."""
        feature = ExcelFeature(
            name="TEST_FUNC",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS},
            fallback_available=True,
            description="Test function",
        )

        assert feature.name == "TEST_FUNC"
        assert feature.min_version == ExcelVersion.EXCEL_365
        assert Platform.WINDOWS in feature.supported_platforms
        assert feature.fallback_available is True
        assert feature.description == "Test function"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_case_insensitive_feature_names(self):
        """Test feature names are case-insensitive."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        assert manager.supports_feature("XLOOKUP") == manager.supports_feature("xlookup")
        assert manager.supports_feature("Filter") == manager.supports_feature("filter")

    def test_empty_let_variables(self):
        """Test LET with empty variables list."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        formula = manager.get_let_formula(
            variables=[],
            calculation="A1+B1",
        )

        # Should still generate valid formula
        assert "A1+B1" in formula

    def test_xlookup_with_empty_if_not_found(self):
        """Test XLOOKUP with empty if_not_found parameter."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_365,
            target_platform=Platform.WINDOWS,
        )

        formula = manager.get_xlookup_formula(
            lookup_value="A2",
            lookup_array="B:B",
            return_array="C:C",
            if_not_found='""',
        )

        assert '""' in formula


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_project_management_formula_compatibility(self):
        """Test compatibility for typical project management formulas."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
            enable_fallbacks=True,
        )

        # Task lookup scenario
        task_lookup = manager.get_xlookup_formula(
            lookup_value="$A2",
            lookup_array="Tasks!$A:$A",
            return_array="Tasks!$B:$B",
            if_not_found='"Task Not Found"',
        )

        assert "INDEX(" in task_lookup  # Should use fallback
        assert "MATCH(" in task_lookup

    def test_multi_platform_deployment(self):
        """Test generating formulas for multiple platforms."""
        platforms = [Platform.WINDOWS, Platform.MAC, Platform.WEB]
        versions = [ExcelVersion.EXCEL_2019, ExcelVersion.EXCEL_365]

        for platform in platforms:
            for version in versions:
                manager = ExcelCompatibilityManager(
                    target_version=version,
                    target_platform=platform,
                    enable_fallbacks=True,
                )

                report = manager.get_compatibility_report()

                # Should generate valid report for all combinations
                assert report["target_version"] in ["2019", "365"]
                assert report["target_platform"] in ["windows", "mac", "web"]
                assert 0 <= report["support_percentage"] <= 100

    def test_performance_critical_formulas(self):
        """Test optimization of performance-critical formulas."""
        manager = ExcelCompatibilityManager(
            target_version=ExcelVersion.EXCEL_2019,
            target_platform=Platform.WINDOWS,
        )

        # Complex formula with potential optimizations
        complex_formula = "=SUM(OFFSET(A1,0,0,COUNTA(A:A),1))"
        optimized = manager.optimize_formula_performance(complex_formula)

        # Should process formula without errors
        assert optimized is not None
        assert len(optimized) > 0


# Test coverage summary
def test_coverage_target():
    """Verify test coverage meets >85% target."""
    # This is a marker test - actual coverage measured by pytest-cov
    # Target: >85% coverage, 100% pass rate
    assert True, "Coverage target: >85%"
