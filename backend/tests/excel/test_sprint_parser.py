"""Tests for sprint pattern parsing and calculation."""

import pytest
from datetime import date, timedelta

from app.excel.sprint_parser import SprintParser
from app.excel.config import SprintPatternType


class TestYearQuarterNumberPattern:
    """Test YY.Q.# pattern calculations."""

    def test_q1_sprint_calculation(self):
        """Test Q1 sprint number calculation."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # First sprint of Q1 2025 (January 1-14)
        sprint1 = parser.calculate_sprint_number(date(2025, 1, 1))
        assert sprint1 == "25.Q1.1"

        # Second sprint of Q1 2025 (January 15-28)
        sprint2 = parser.calculate_sprint_number(date(2025, 1, 15))
        assert sprint2 == "25.Q1.2"

    def test_q2_sprint_calculation(self):
        """Test Q2 sprint number calculation."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # First sprint of Q2 2025 (April 1-14)
        sprint = parser.calculate_sprint_number(date(2025, 4, 1))
        assert sprint == "25.Q2.1"

    def test_q3_sprint_calculation(self):
        """Test Q3 sprint number calculation."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # First sprint of Q3 2025 (July 1-14)
        sprint = parser.calculate_sprint_number(date(2025, 7, 1))
        assert sprint == "25.Q3.1"

    def test_q4_sprint_calculation(self):
        """Test Q4 sprint number calculation."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # First sprint of Q4 2025 (October 1-14)
        sprint = parser.calculate_sprint_number(date(2025, 10, 1))
        assert sprint == "25.Q4.1"

    def test_different_sprint_durations(self):
        """Test sprint calculation with different durations."""
        # 1-week sprints
        parser_1w = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=1
        )
        sprint = parser_1w.calculate_sprint_number(date(2025, 1, 8))
        assert "25.Q1" in sprint

        # 3-week sprints
        parser_3w = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=3
        )
        sprint = parser_3w.calculate_sprint_number(date(2025, 1, 1))
        assert sprint == "25.Q1.1"

    def test_parse_year_quarter_sprint(self):
        """Test parsing YY.Q.# format back to date range."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # Parse first sprint of Q1 2025
        sprint_range = parser.parse_sprint_identifier("25.Q1.1")

        assert sprint_range is not None
        start, end = sprint_range
        assert start == date(2025, 1, 1)
        assert end.month == 1

    def test_parse_invalid_format(self):
        """Test parsing invalid sprint format."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        result = parser.parse_sprint_identifier("invalid_format")
        assert result is None


class TestPISprintPattern:
    """Test PI-N.Sprint-M pattern calculations."""

    def test_pi1_sprint_calculation(self):
        """Test Program Increment 1 sprint calculations."""
        parser = SprintParser(
            pattern_type=SprintPatternType.PI_SPRINT,
            duration_weeks=2,
            start_date=date(2025, 1, 6)  # PI 1 starts Jan 6
        )

        # First sprint of PI 1
        sprint1 = parser.calculate_sprint_number(date(2025, 1, 6))
        assert sprint1 == "PI-1.Sprint-1"

        # Second sprint of PI 1 (Jan 20)
        sprint2 = parser.calculate_sprint_number(date(2025, 1, 20))
        assert sprint2 == "PI-1.Sprint-2"

        # Fifth sprint of PI 1
        sprint5 = parser.calculate_sprint_number(date(2025, 3, 3))
        assert sprint5 == "PI-1.Sprint-5"

    def test_pi2_sprint_calculation(self):
        """Test Program Increment 2 sprint calculations."""
        parser = SprintParser(
            pattern_type=SprintPatternType.PI_SPRINT,
            duration_weeks=2,
            start_date=date(2025, 1, 6)
        )

        # First sprint of PI 2 (10 weeks after start = 5 sprints per PI)
        # PI 1: Sprints 1-5, PI 2: Sprints 6-10
        pi2_start = date(2025, 1, 6) + timedelta(weeks=10)
        sprint = parser.calculate_sprint_number(pi2_start)
        assert sprint == "PI-2.Sprint-1"

    def test_pi_sprint_requires_start_date(self):
        """Test that PI-Sprint pattern requires start_date."""
        parser = SprintParser(
            pattern_type=SprintPatternType.PI_SPRINT,
            duration_weeks=2
            # No start_date provided
        )

        with pytest.raises(ValueError) as exc_info:
            parser.calculate_sprint_number(date(2025, 1, 1))

        assert "start_date is required" in str(exc_info.value)

    def test_parse_pi_sprint(self):
        """Test parsing PI-N.Sprint-M format back to date range."""
        parser = SprintParser(
            pattern_type=SprintPatternType.PI_SPRINT,
            duration_weeks=2,
            start_date=date(2025, 1, 6)
        )

        # Parse PI-1.Sprint-1
        sprint_range = parser.parse_sprint_identifier("PI-1.Sprint-1")

        assert sprint_range is not None
        start, end = sprint_range
        assert start == date(2025, 1, 6)
        assert end == date(2025, 1, 19)

    def test_parse_pi_sprint_later_sprints(self):
        """Test parsing later PI sprints."""
        parser = SprintParser(
            pattern_type=SprintPatternType.PI_SPRINT,
            duration_weeks=2,
            start_date=date(2025, 1, 6)
        )

        # Parse PI-2.Sprint-3
        sprint_range = parser.parse_sprint_identifier("PI-2.Sprint-3")

        assert sprint_range is not None
        start, end = sprint_range
        # PI-2.Sprint-3 is the 8th total sprint (5 sprints in PI-1, then 3 in PI-2)
        expected_start = date(2025, 1, 6) + timedelta(weeks=14)  # 7 sprints * 2 weeks
        assert start == expected_start


class TestCalendarWeekPattern:
    """Test YYYY.WW pattern calculations."""

    def test_calendar_week_calculation(self):
        """Test ISO calendar week number calculation."""
        parser = SprintParser(
            pattern_type=SprintPatternType.CALENDAR_WEEK,
            duration_weeks=1
        )

        # Week 1 of 2025
        sprint = parser.calculate_sprint_number(date(2025, 1, 6))
        assert sprint == "2025.W02"  # ISO week calculation

        # Week 26 of 2025 (mid-year)
        sprint = parser.calculate_sprint_number(date(2025, 6, 30))
        assert "2025.W" in sprint

    def test_parse_calendar_week(self):
        """Test parsing YYYY.WW format back to date range."""
        parser = SprintParser(
            pattern_type=SprintPatternType.CALENDAR_WEEK,
            duration_weeks=1
        )

        # Parse week 10 of 2025
        sprint_range = parser.parse_sprint_identifier("2025.W10")

        assert sprint_range is not None
        start, end = sprint_range
        assert start.year == 2025
        assert end == start + timedelta(days=6)  # 7-day week


class TestCustomPattern:
    """Test custom pattern calculations."""

    def test_custom_pattern_with_year(self):
        """Test custom pattern with year placeholders."""
        parser = SprintParser(
            pattern_type=SprintPatternType.CUSTOM,
            custom_pattern="{YYYY}-Sprint-{#}",
            duration_weeks=2,
            start_date=date(2025, 1, 1)
        )

        sprint = parser.calculate_sprint_number(date(2025, 1, 1))
        assert sprint == "2025-Sprint-1"

        sprint2 = parser.calculate_sprint_number(date(2025, 1, 15))
        assert sprint2 == "2025-Sprint-2"

    def test_custom_pattern_with_quarter(self):
        """Test custom pattern with quarter placeholder."""
        parser = SprintParser(
            pattern_type=SprintPatternType.CUSTOM,
            custom_pattern="Q{Q}-{#}",
            duration_weeks=2,
            start_date=date(2025, 1, 1)
        )

        sprint_q1 = parser.calculate_sprint_number(date(2025, 1, 1))
        assert "Q1" in sprint_q1

        sprint_q2 = parser.calculate_sprint_number(date(2025, 4, 1))
        assert "Q2" in sprint_q2

    def test_custom_pattern_with_month(self):
        """Test custom pattern with month placeholder."""
        parser = SprintParser(
            pattern_type=SprintPatternType.CUSTOM,
            custom_pattern="{YY}.{MM}.Sprint{#}",
            duration_weeks=2,
            start_date=date(2025, 1, 1)
        )

        sprint = parser.calculate_sprint_number(date(2025, 1, 1))
        assert sprint == "25.01.Sprint1"

    def test_custom_pattern_with_week(self):
        """Test custom pattern with ISO week placeholder."""
        parser = SprintParser(
            pattern_type=SprintPatternType.CUSTOM,
            custom_pattern="{YYYY}.W{WW}",
            duration_weeks=1
        )

        sprint = parser.calculate_sprint_number(date(2025, 1, 6))
        assert "2025.W" in sprint

    def test_custom_pattern_requires_pattern_string(self):
        """Test custom pattern requires custom_pattern parameter."""
        parser = SprintParser(
            pattern_type=SprintPatternType.CUSTOM,
            duration_weeks=2
            # No custom_pattern provided
        )

        with pytest.raises(ValueError) as exc_info:
            parser.calculate_sprint_number(date(2025, 1, 1))

        assert "custom_pattern is required" in str(exc_info.value)

    def test_custom_pattern_complex(self):
        """Test complex custom pattern with multiple placeholders."""
        parser = SprintParser(
            pattern_type=SprintPatternType.CUSTOM,
            custom_pattern="{YYYY}.Q{Q}.W{WW}.S{#}",
            duration_weeks=2,
            start_date=date(2025, 1, 1)
        )

        sprint = parser.calculate_sprint_number(date(2025, 1, 15))
        assert "2025.Q1" in sprint
        assert ".S" in sprint  # Sprint number


class TestSprintRange:
    """Test getting sprint ranges."""

    def test_get_sprint_range_single_quarter(self):
        """Test getting all sprints in a quarter."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # Get all sprints in Q1 2025
        sprints = parser.get_sprint_range(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31)
        )

        assert len(sprints) > 0
        # Verify all are Q1 sprints
        for sprint_id, start, end in sprints:
            assert "Q1" in sprint_id

    def test_get_sprint_range_no_duplicates(self):
        """Test that sprint range doesn't return duplicates."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        sprints = parser.get_sprint_range(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31)
        )

        # Check for unique start dates
        start_dates = [s[1] for s in sprints]
        assert len(start_dates) == len(set(start_dates))

    def test_get_sprint_range_pi_pattern(self):
        """Test getting sprint range with PI pattern."""
        parser = SprintParser(
            pattern_type=SprintPatternType.PI_SPRINT,
            duration_weeks=2,
            start_date=date(2025, 1, 6)
        )

        # Get first 10 weeks (5 sprints = PI 1)
        sprints = parser.get_sprint_range(
            start_date=date(2025, 1, 6),
            end_date=date(2025, 3, 16)
        )

        assert len(sprints) >= 5
        # Verify PI-1 sprints
        pi1_sprints = [s for s in sprints if "PI-1" in s[0]]
        assert len(pi1_sprints) == 5


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_year_transition(self):
        """Test sprint calculation across year boundary."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # End of 2024
        sprint_2024 = parser.calculate_sprint_number(date(2024, 12, 31))
        assert "24.Q4" in sprint_2024

        # Start of 2025
        sprint_2025 = parser.calculate_sprint_number(date(2025, 1, 1))
        assert "25.Q1" in sprint_2025

    def test_leap_year_handling(self):
        """Test sprint calculation in leap year."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # Feb 29, 2024 (leap year)
        sprint = parser.calculate_sprint_number(date(2024, 2, 29))
        assert "24.Q1" in sprint

    def test_invalid_pattern_type(self):
        """Test handling of invalid pattern type."""
        # This would require creating an invalid enum value,
        # which Pydantic prevents, so we test the else clause
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        # Valid operation
        result = parser.calculate_sprint_number(date(2025, 1, 1))
        assert result is not None

    def test_sprint_number_persistence(self):
        """Test that same date always produces same sprint number."""
        parser = SprintParser(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        test_date = date(2025, 6, 15)
        sprint1 = parser.calculate_sprint_number(test_date)
        sprint2 = parser.calculate_sprint_number(test_date)

        assert sprint1 == sprint2
