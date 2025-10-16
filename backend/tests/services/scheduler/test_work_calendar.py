"""
Tests for WorkCalendar implementation.

Tests holiday handling, weekend skipping, and working day calculations.
"""

import pytest
from datetime import date, timedelta
from app.services.scheduler.work_calendar import WorkCalendar


class TestWorkCalendarBasics:
    """Test basic WorkCalendar functionality."""

    def test_default_calendar_monday_to_friday(self):
        """Test that default calendar treats Monday-Friday as working days."""
        calendar = WorkCalendar()

        # Monday (2025-01-13)
        assert calendar.is_working_day(date(2025, 1, 13)) is True
        # Tuesday
        assert calendar.is_working_day(date(2025, 1, 14)) is True
        # Wednesday
        assert calendar.is_working_day(date(2025, 1, 15)) is True
        # Thursday
        assert calendar.is_working_day(date(2025, 1, 16)) is True
        # Friday
        assert calendar.is_working_day(date(2025, 1, 17)) is True

    def test_default_calendar_weekends_not_working(self):
        """Test that default calendar treats Saturday-Sunday as non-working."""
        calendar = WorkCalendar()

        # Saturday (2025-01-18)
        assert calendar.is_working_day(date(2025, 1, 18)) is False
        # Sunday (2025-01-19)
        assert calendar.is_working_day(date(2025, 1, 19)) is False

    def test_holiday_not_working_day(self):
        """Test that holidays are not working days."""
        holidays = [date(2025, 1, 1)]  # New Year's Day
        calendar = WorkCalendar(holidays=holidays)

        # Wednesday, but a holiday
        assert calendar.is_working_day(date(2025, 1, 1)) is False

    def test_custom_workdays(self):
        """Test custom workday configuration (e.g., Sunday-Thursday)."""
        # Middle East schedule: Sunday-Thursday
        calendar = WorkCalendar(workdays={6, 0, 1, 2, 3})  # Sun-Thu

        # Sunday (2025-01-19) - working
        assert calendar.is_working_day(date(2025, 1, 19)) is True
        # Friday (2025-01-17) - not working
        assert calendar.is_working_day(date(2025, 1, 17)) is False
        # Saturday (2025-01-18) - not working
        assert calendar.is_working_day(date(2025, 1, 18)) is False


class TestAddWorkingDays:
    """Test add_working_days function."""

    def test_add_working_days_no_weekends(self):
        """Test adding working days without crossing weekend."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)  # Monday

        # Add 3 working days: Mon → Thu
        result = calendar.add_working_days(start, 3.0)
        assert result == date(2025, 1, 16)  # Thursday

    def test_add_working_days_skip_weekend(self):
        """Test adding working days skips weekend."""
        calendar = WorkCalendar()
        start = date(2025, 1, 16)  # Thursday

        # Add 3 working days: Thu → Fri → Mon → Tue
        result = calendar.add_working_days(start, 3.0)
        assert result == date(2025, 1, 21)  # Tuesday

    def test_add_working_days_skip_holiday(self):
        """Test adding working days skips holidays."""
        holidays = [date(2025, 1, 15)]  # Wednesday holiday
        calendar = WorkCalendar(holidays=holidays)
        start = date(2025, 1, 13)  # Monday

        # Add 3 working days: Mon → Tue → Thu → Fri (skip Wed holiday)
        result = calendar.add_working_days(start, 3.0)
        assert result == date(2025, 1, 17)  # Friday

    def test_add_working_days_fractional_days(self):
        """Test adding fractional working days."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)  # Monday

        # Add 2.5 working days: Mon → Wed + 0.5 days
        result = calendar.add_working_days(start, 2.5)
        expected = date(2025, 1, 15) + timedelta(days=0.5)
        assert result == expected

    def test_add_working_days_zero_days(self):
        """Test adding zero working days returns start date."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)

        result = calendar.add_working_days(start, 0.0)
        assert result == start

    def test_add_working_days_one_day(self):
        """Test adding exactly one working day."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)  # Monday

        result = calendar.add_working_days(start, 1.0)
        assert result == date(2025, 1, 14)  # Tuesday

    def test_add_working_days_across_multiple_weekends(self):
        """Test adding many working days across multiple weekends."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)  # Monday

        # Add 10 working days (2 full weeks)
        result = calendar.add_working_days(start, 10.0)
        assert result == date(2025, 1, 27)  # Monday, 2 weeks later

    def test_add_working_days_starting_on_weekend(self):
        """Test that starting on weekend still works correctly."""
        calendar = WorkCalendar()
        start = date(2025, 1, 18)  # Saturday

        # Add 1 working day: Sat → Mon (skip Sat, Sun)
        result = calendar.add_working_days(start, 1.0)
        assert result == date(2025, 1, 20)  # Monday

    def test_add_working_days_large_number(self):
        """Test adding large number of working days (60 days = 12 weeks)."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)  # Monday

        # Add 60 working days
        result = calendar.add_working_days(start, 60.0)
        # 60 working days = 12 weeks = 84 calendar days
        expected = date(2025, 4, 7)  # Monday, ~3 months later
        assert result == expected


class TestCountWorkingDays:
    """Test count_working_days function."""

    def test_count_working_days_simple_week(self):
        """Test counting working days in simple week."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)  # Monday
        end = date(2025, 1, 17)  # Friday

        count = calendar.count_working_days(start, end)
        assert count == 5  # Mon-Fri

    def test_count_working_days_includes_weekend(self):
        """Test counting working days across weekend."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)  # Monday
        end = date(2025, 1, 20)  # Next Monday

        count = calendar.count_working_days(start, end)
        assert count == 6  # Mon-Fri + Mon (skip Sat-Sun)

    def test_count_working_days_with_holiday(self):
        """Test counting working days with holiday."""
        holidays = [date(2025, 1, 15)]  # Wednesday
        calendar = WorkCalendar(holidays=holidays)
        start = date(2025, 1, 13)  # Monday
        end = date(2025, 1, 17)  # Friday

        count = calendar.count_working_days(start, end)
        assert count == 4  # Mon, Tue, Thu, Fri (skip Wed holiday)

    def test_count_working_days_same_day(self):
        """Test counting working days when start equals end."""
        calendar = WorkCalendar()
        day = date(2025, 1, 13)  # Monday

        count = calendar.count_working_days(day, day)
        assert count == 1  # Same day counts as 1

    def test_count_working_days_end_before_start(self):
        """Test that end before start raises error."""
        calendar = WorkCalendar()
        start = date(2025, 1, 20)
        end = date(2025, 1, 13)

        with pytest.raises(ValueError, match="End date.*before start date"):
            calendar.count_working_days(start, end)


class TestTaskDateCalculation:
    """Test task date calculation with calendar."""

    def test_calculate_task_dates_single_task(self):
        """Test calculating dates for single task."""
        from app.services.scheduler.task_graph import TaskGraph
        from app.services.scheduler.cpm import calculate_critical_path
        from app.services.scheduler.work_calendar import calculate_task_dates

        calendar = WorkCalendar()
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        durations = {"T001": 5.0}

        schedule = calculate_critical_path(graph, durations)
        project_start = date(2025, 1, 13)  # Monday

        task_dates = calculate_task_dates(schedule, project_start, calendar)

        # 5 working days: Mon-Fri
        assert task_dates["T001"] == (date(2025, 1, 13), date(2025, 1, 17))

    def test_calculate_task_dates_sequence_with_weekends(self):
        """Test calculating dates for sequence crossing weekend."""
        from app.services.scheduler.task_graph import TaskGraph
        from app.services.scheduler.cpm import calculate_critical_path
        from app.services.scheduler.work_calendar import calculate_task_dates

        calendar = WorkCalendar()
        graph = TaskGraph()
        graph.add_node("T001", duration=3.0)
        graph.add_node("T002", duration=5.0)
        graph.add_edge("T001", "T002")

        durations = {"T001": 3.0, "T002": 5.0}
        schedule = calculate_critical_path(graph, durations)
        project_start = date(2025, 1, 16)  # Thursday

        task_dates = calculate_task_dates(schedule, project_start, calendar)

        # T001: Thu-Fri-Mon (3 working days)
        assert task_dates["T001"] == (date(2025, 1, 16), date(2025, 1, 20))
        # T002: Tue-Mon (5 working days, starts day after T001 ends)
        # ES=3.0 means add 3 complete working days from project start (Thu→Fri→Mon→Tue)
        assert task_dates["T002"] == (date(2025, 1, 21), date(2025, 1, 27))

    def test_calculate_task_dates_parallel_tasks(self):
        """Test calculating dates for parallel tasks."""
        from app.services.scheduler.task_graph import TaskGraph
        from app.services.scheduler.cpm import calculate_critical_path
        from app.services.scheduler.work_calendar import calculate_task_dates

        calendar = WorkCalendar()
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        graph.add_node("T002", duration=3.0)
        graph.add_node("T003", duration=7.0)
        graph.add_edge("T001", "T002")
        graph.add_edge("T001", "T003")

        durations = {"T001": 5.0, "T002": 3.0, "T003": 7.0}
        schedule = calculate_critical_path(graph, durations)
        project_start = date(2025, 1, 13)  # Monday

        task_dates = calculate_task_dates(schedule, project_start, calendar)

        # T001: Mon-Fri (5 days)
        assert task_dates["T001"] == (date(2025, 1, 13), date(2025, 1, 17))
        # T002 and T003 both start Mon after T001 finishes Fri
        assert task_dates["T002"][0] == date(2025, 1, 20)
        assert task_dates["T003"][0] == date(2025, 1, 20)

    def test_calculate_task_dates_with_holidays(self):
        """Test calculating dates with holidays."""
        from app.services.scheduler.task_graph import TaskGraph
        from app.services.scheduler.cpm import calculate_critical_path
        from app.services.scheduler.work_calendar import calculate_task_dates

        holidays = [date(2025, 1, 15)]  # Wednesday
        calendar = WorkCalendar(holidays=holidays)
        graph = TaskGraph()
        graph.add_node("T001", duration=5.0)
        durations = {"T001": 5.0}

        schedule = calculate_critical_path(graph, durations)
        project_start = date(2025, 1, 13)  # Monday

        task_dates = calculate_task_dates(schedule, project_start, calendar)

        # 5 working days, skipping Wed holiday: Mon, Tue, Thu, Fri, Mon
        assert task_dates["T001"] == (date(2025, 1, 13), date(2025, 1, 20))


class TestWorkCalendarEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_calendar_with_many_holidays(self):
        """Test calendar with many holidays."""
        holidays = [
            date(2025, 1, 1),  # New Year
            date(2025, 1, 20),  # MLK Day
            date(2025, 2, 17),  # Presidents Day
            date(2025, 5, 26),  # Memorial Day
            date(2025, 7, 4),  # Independence Day
        ]
        calendar = WorkCalendar(holidays=holidays)

        # Verify all holidays are non-working
        for holiday in holidays:
            assert calendar.is_working_day(holiday) is False

    def test_add_working_days_fractional_precision(self):
        """Test fractional day precision (0.5, 0.25, etc.)."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)

        # 0.5 days
        result = calendar.add_working_days(start, 0.5)
        expected = date(2025, 1, 13) + timedelta(days=0.5)
        assert result == expected

        # 0.25 days
        result = calendar.add_working_days(start, 0.25)
        expected = date(2025, 1, 13) + timedelta(days=0.25)
        assert result == expected

    def test_calendar_empty_holidays_list(self):
        """Test calendar with empty holidays list."""
        calendar = WorkCalendar(holidays=[])

        # Should work same as default
        assert calendar.is_working_day(date(2025, 1, 13)) is True

    def test_calendar_none_holidays(self):
        """Test calendar with None holidays."""
        calendar = WorkCalendar(holidays=None)

        # Should work same as default
        assert calendar.is_working_day(date(2025, 1, 13)) is True

    def test_add_working_days_very_small_fraction(self):
        """Test adding very small fraction (0.1 days = 0.8 hours)."""
        calendar = WorkCalendar()
        start = date(2025, 1, 13)

        result = calendar.add_working_days(start, 0.1)
        expected = date(2025, 1, 13) + timedelta(days=0.1)
        assert result == expected
