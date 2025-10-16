"""
Tests for dependency text parsing.

Tests parsing dependency strings like "T001,T002" into lists of task IDs,
with validation for format errors and edge cases.
"""

import pytest
from app.services.scheduler.dependency_parser import (
    parse_dependencies,
    DependencyParseError,
)


class TestDependencyParserBasics:
    """Test basic dependency parsing functionality."""

    def test_parse_single_dependency(self):
        """Test parsing single dependency."""
        result = parse_dependencies("T001")
        assert result == ["T001"]

    def test_parse_multiple_dependencies(self):
        """Test parsing multiple dependencies."""
        result = parse_dependencies("T001,T002,T003")
        assert result == ["T001", "T002", "T003"]

    def test_parse_dependencies_with_spaces(self):
        """Test parsing dependencies with spaces around commas."""
        result = parse_dependencies("T001, T002, T003")
        assert result == ["T001", "T002", "T003"]

    def test_parse_dependencies_mixed_spacing(self):
        """Test parsing dependencies with inconsistent spacing."""
        result = parse_dependencies("T001,T002, T003 ,T004")
        assert result == ["T001", "T002", "T003", "T004"]

    def test_parse_empty_string(self):
        """Test parsing empty string returns empty list."""
        result = parse_dependencies("")
        assert result == []

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string returns empty list."""
        result = parse_dependencies("   ")
        assert result == []

    def test_parse_none_input(self):
        """Test parsing None returns empty list."""
        result = parse_dependencies(None)
        assert result == []


class TestDependencyParserValidation:
    """Test validation and error handling."""

    def test_reject_invalid_task_id_format(self):
        """Test rejection of task IDs not matching expected format."""
        # Task IDs with spaces are invalid (alphanumeric, underscore, hyphen only)
        with pytest.raises(DependencyParseError, match="Invalid task ID format"):
            parse_dependencies("task 1,task 2")

    def test_reject_empty_task_id(self):
        """Test rejection of empty task IDs after comma."""
        with pytest.raises(DependencyParseError, match="Empty task ID"):
            parse_dependencies("T001,,T003")

    def test_reject_trailing_comma(self):
        """Test rejection of trailing comma."""
        with pytest.raises(DependencyParseError, match="Empty task ID"):
            parse_dependencies("T001,T002,")

    def test_reject_leading_comma(self):
        """Test rejection of leading comma."""
        with pytest.raises(DependencyParseError, match="Empty task ID"):
            parse_dependencies(",T001,T002")

    def test_reject_special_characters(self):
        """Test rejection of special characters in task IDs."""
        with pytest.raises(DependencyParseError, match="Invalid task ID format"):
            parse_dependencies("T001,T@02,T003")

    def test_reject_whitespace_in_task_id(self):
        """Test rejection of whitespace within task ID."""
        with pytest.raises(DependencyParseError, match="Invalid task ID format"):
            parse_dependencies("T001,T 002,T003")


class TestDependencyParserFormats:
    """Test various task ID formats."""

    def test_parse_numeric_only_ids(self):
        """Test parsing task IDs with only numbers."""
        result = parse_dependencies("T001,T002,T999")
        assert result == ["T001", "T002", "T999"]

    def test_parse_alphanumeric_ids(self):
        """Test parsing task IDs with letters and numbers."""
        result = parse_dependencies("TASK001,TASK002,TASK999")
        assert result == ["TASK001", "TASK002", "TASK999"]

    def test_parse_short_ids(self):
        """Test parsing short task IDs."""
        result = parse_dependencies("T1,T2,T3")
        assert result == ["T1", "T2", "T3"]

    def test_parse_long_ids(self):
        """Test parsing long task IDs."""
        result = parse_dependencies("LONGPREFIX001,LONGPREFIX002")
        assert result == ["LONGPREFIX001", "LONGPREFIX002"]

    def test_parse_mixed_length_ids(self):
        """Test parsing task IDs of mixed lengths."""
        result = parse_dependencies("T1,TASK001,PREFIX_TASK_001")
        assert result == ["T1", "TASK001", "PREFIX_TASK_001"]

    def test_parse_ids_with_underscores(self):
        """Test parsing task IDs with underscores."""
        result = parse_dependencies("TASK_001,TASK_002")
        assert result == ["TASK_001", "TASK_002"]

    def test_parse_ids_with_hyphens(self):
        """Test parsing task IDs with hyphens."""
        result = parse_dependencies("TASK-001,TASK-002")
        assert result == ["TASK-001", "TASK-002"]


class TestDependencyParserEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_parse_many_dependencies(self):
        """Test parsing large number of dependencies."""
        deps = ",".join(f"T{i:03d}" for i in range(1, 101))
        result = parse_dependencies(deps)
        assert len(result) == 100
        assert result[0] == "T001"
        assert result[-1] == "T100"

    def test_parse_single_character_id(self):
        """Test parsing single character task ID."""
        result = parse_dependencies("A,B,C")
        assert result == ["A", "B", "C"]

    def test_preserve_order(self):
        """Test that parsing preserves dependency order."""
        result = parse_dependencies("T003,T001,T002")
        assert result == ["T003", "T001", "T002"]

    def test_allow_duplicate_dependencies(self):
        """Test that duplicates are allowed (caller handles deduplication if needed)."""
        result = parse_dependencies("T001,T002,T001")
        assert result == ["T001", "T002", "T001"]

    def test_case_sensitive_ids(self):
        """Test that task IDs are case-sensitive."""
        result = parse_dependencies("T001,t001,T001")
        assert result == ["T001", "t001", "T001"]

    def test_maximum_reasonable_id_length(self):
        """Test parsing very long task IDs (reasonable upper bound)."""
        long_id = "VERY_LONG_TASK_IDENTIFIER_WITH_MANY_CHARACTERS_001"
        result = parse_dependencies(f"{long_id},{long_id}2")
        assert result == [long_id, f"{long_id}2"]
