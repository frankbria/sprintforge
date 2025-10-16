"""
Work calendar implementation for project scheduling.

Handles holidays, weekends, and working day calculations for converting
task durations into calendar dates.
"""

from typing import List, Set, Dict, Tuple, Optional
from datetime import date, timedelta
from app.services.scheduler.models import CriticalPathResult


class WorkCalendar:
    """
    Work calendar for managing working days and holidays.

    Supports:
    - Configurable workdays (default: Monday-Friday)
    - Holiday handling
    - Working day calculations
    - Calendar date conversions

    Attributes:
        holidays: Set of holiday dates
        workdays: Set of weekday numbers (0=Monday, 6=Sunday)
    """

    def __init__(
        self,
        holidays: Optional[List[date]] = None,
        workdays: Optional[Set[int]] = None,
    ):
        """
        Initialize work calendar.

        Args:
            holidays: List of holiday dates (non-working days)
            workdays: Set of working weekday numbers (0=Mon, 6=Sun)
                     Default is {0,1,2,3,4} for Monday-Friday
        """
        self.holidays = set(holidays or [])
        self.workdays = workdays if workdays is not None else {0, 1, 2, 3, 4}

    def is_working_day(self, d: date) -> bool:
        """
        Check if date is a working day.

        A working day is one that:
        - Falls on a configured workday (e.g., Monday-Friday)
        - Is not a holiday

        Args:
            d: Date to check

        Returns:
            True if date is a working day, False otherwise
        """
        return d.weekday() in self.workdays and d not in self.holidays

    def add_working_days(self, start_date: date, working_days: float) -> date:
        """
        Add working days to start date, skipping weekends and holidays.

        Supports fractional days (e.g., 2.5 working days).
        Fractional part is added as calendar days (not skipped to next working day).

        Args:
            start_date: Starting date
            working_days: Number of working days to add (can be fractional)

        Returns:
            Date after adding working days
        """
        if working_days == 0:
            return start_date

        # Split into whole days and fractional part
        days_to_add = int(working_days)
        fractional_part = working_days - days_to_add

        current_date = start_date
        added_days = 0

        # Add whole working days
        while added_days < days_to_add:
            current_date += timedelta(days=1)
            if self.is_working_day(current_date):
                added_days += 1

        # Add fractional part as calendar days (not working days)
        if fractional_part > 0:
            current_date += timedelta(days=fractional_part)

        return current_date

    def count_working_days(self, start_date: date, end_date: date) -> int:
        """
        Count working days between start and end dates (inclusive).

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of working days

        Raises:
            ValueError: If end_date is before start_date
        """
        if end_date < start_date:
            raise ValueError(f"End date {end_date} is before start date {start_date}")

        count = 0
        current = start_date

        while current <= end_date:
            if self.is_working_day(current):
                count += 1
            current += timedelta(days=1)

        return count


def calculate_task_dates(
    schedule: CriticalPathResult,
    project_start: date,
    calendar: WorkCalendar,
) -> Dict[str, Tuple[date, date]]:
    """
    Convert task ES/EF working days to actual calendar dates.

    Uses work calendar to skip weekends and holidays when calculating dates.

    Args:
        schedule: CPM schedule result with ES/EF in working days
        project_start: Project start date
        calendar: Work calendar for date calculations

    Returns:
        Dictionary mapping task_id to (start_date, end_date) tuple
    """
    task_dates: Dict[str, Tuple[date, date]] = {}

    for task_id, task_data in schedule.tasks.items():
        # Calculate start date by adding ES working days to project start
        start_date = calendar.add_working_days(project_start, task_data.es)

        # Calculate end date from start date and duration
        # Duration represents how many working days the task occupies
        # Last day = start + (duration - 1) since task occupies [0, duration-1] days
        end_date = calendar.add_working_days(start_date, task_data.duration - 1.0)

        task_dates[task_id] = (start_date, end_date)

    return task_dates
