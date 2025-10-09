"""
Sprint pattern parsing and calculation utilities.

Supports multiple sprint numbering schemes including:
- YY.Q.# (Year.Quarter.Sprint)
- PI-N.Sprint-M (Program Increment N, Sprint M)
- YYYY.WW (Year.Week)
- Custom patterns
"""

import re
from datetime import date, timedelta
from typing import Optional, Tuple
import structlog

from app.excel.config import SprintPatternType

logger = structlog.get_logger(__name__)


class SprintParser:
    """
    Parser for calculating sprint numbers from dates using different patterns.

    Supports multiple sprint numbering schemes and provides bidirectional
    conversion between dates and sprint identifiers.
    """

    def __init__(
        self,
        pattern_type: SprintPatternType,
        duration_weeks: int = 2,
        start_date: Optional[date] = None,
        custom_pattern: Optional[str] = None,
    ):
        """
        Initialize sprint parser with pattern configuration.

        Args:
            pattern_type: Type of sprint numbering pattern
            duration_weeks: Sprint duration in weeks (1-8)
            start_date: First sprint start date (required for some patterns)
            custom_pattern: Custom pattern string if using CUSTOM type
        """
        self.pattern_type = pattern_type
        self.duration_weeks = duration_weeks
        self.start_date = start_date
        self.custom_pattern = custom_pattern

        logger.debug(
            "Sprint parser initialized",
            pattern_type=pattern_type.value,
            duration_weeks=duration_weeks,
        )

    def calculate_sprint_number(self, target_date: date) -> str:
        """
        Calculate sprint number for a given date.

        Args:
            target_date: Date to calculate sprint number for

        Returns:
            Sprint identifier string (e.g., "25.Q1.3", "PI-2.Sprint-4")

        Raises:
            ValueError: If pattern requires start_date but it's not set
        """
        if self.pattern_type == SprintPatternType.YEAR_QUARTER_NUMBER:
            return self._calculate_year_quarter_sprint(target_date)
        elif self.pattern_type == SprintPatternType.PI_SPRINT:
            return self._calculate_pi_sprint(target_date)
        elif self.pattern_type == SprintPatternType.CALENDAR_WEEK:
            return self._calculate_calendar_week(target_date)
        elif self.pattern_type == SprintPatternType.CUSTOM:
            return self._calculate_custom_pattern(target_date)
        else:
            raise ValueError(f"Unsupported pattern type: {self.pattern_type}")

    def _calculate_year_quarter_sprint(self, target_date: date) -> str:
        """Calculate YY.Q.# pattern sprint number."""
        year = target_date.year % 100  # Last 2 digits of year
        quarter = (target_date.month - 1) // 3 + 1  # Quarter (1-4)

        # Calculate quarter start date
        quarter_start_month = (quarter - 1) * 3 + 1
        quarter_start = date(target_date.year, quarter_start_month, 1)

        # Calculate weeks into quarter
        days_into_quarter = (target_date - quarter_start).days
        weeks_into_quarter = days_into_quarter // 7

        # Calculate sprint number within quarter
        sprint_in_quarter = (weeks_into_quarter // self.duration_weeks) + 1

        return f"{year:02d}.Q{quarter}.{sprint_in_quarter}"

    def _calculate_pi_sprint(self, target_date: date) -> str:
        """Calculate PI-N.Sprint-M pattern sprint number."""
        if not self.start_date:
            raise ValueError("start_date is required for PI-Sprint pattern")

        # Calculate days since start
        days_since_start = (target_date - self.start_date).days

        # SAFe typically uses 5 sprints per PI (Program Increment)
        sprints_per_pi = 5
        total_sprints = (days_since_start // (self.duration_weeks * 7)) + 1

        # Calculate PI and sprint within PI
        pi_number = ((total_sprints - 1) // sprints_per_pi) + 1
        sprint_in_pi = ((total_sprints - 1) % sprints_per_pi) + 1

        return f"PI-{pi_number}.Sprint-{sprint_in_pi}"

    def _calculate_calendar_week(self, target_date: date) -> str:
        """Calculate YYYY.WW pattern (ISO week number)."""
        year, week, _ = target_date.isocalendar()
        return f"{year}.W{week:02d}"

    def _calculate_custom_pattern(self, target_date: date) -> str:
        """
        Calculate custom pattern sprint number.

        Custom patterns can use placeholders:
        - {YYYY}: Full year
        - {YY}: Two-digit year
        - {Q}: Quarter (1-4)
        - {MM}: Month (01-12)
        - {WW}: ISO week number
        - {#}: Sprint number from start_date
        """
        if not self.custom_pattern:
            raise ValueError("custom_pattern is required for CUSTOM pattern type")

        pattern = self.custom_pattern
        year = target_date.year
        quarter = (target_date.month - 1) // 3 + 1
        month = target_date.month
        _, week, _ = target_date.isocalendar()

        # Calculate sprint number if start_date is provided
        sprint_num = 1
        if self.start_date:
            days_since_start = (target_date - self.start_date).days
            sprint_num = (days_since_start // (self.duration_weeks * 7)) + 1

        # Replace placeholders
        result = pattern
        result = result.replace("{YYYY}", str(year))
        result = result.replace("{YY}", f"{year % 100:02d}")
        result = result.replace("{Q}", str(quarter))
        result = result.replace("{MM}", f"{month:02d}")
        result = result.replace("{WW}", f"{week:02d}")
        result = result.replace("{#}", str(sprint_num))

        return result

    def parse_sprint_identifier(self, sprint_id: str) -> Optional[Tuple[date, date]]:
        """
        Parse sprint identifier back to date range.

        Args:
            sprint_id: Sprint identifier (e.g., "25.Q1.3")

        Returns:
            Tuple of (start_date, end_date) for the sprint, or None if invalid
        """
        try:
            if self.pattern_type == SprintPatternType.YEAR_QUARTER_NUMBER:
                return self._parse_year_quarter_sprint(sprint_id)
            elif self.pattern_type == SprintPatternType.PI_SPRINT:
                return self._parse_pi_sprint(sprint_id)
            elif self.pattern_type == SprintPatternType.CALENDAR_WEEK:
                return self._parse_calendar_week(sprint_id)
            else:
                logger.warning(
                    "Sprint parsing not supported for pattern type",
                    pattern_type=self.pattern_type.value,
                )
                return None
        except (ValueError, IndexError) as e:
            logger.error("Failed to parse sprint identifier", sprint_id=sprint_id, error=str(e))
            return None

    def _parse_year_quarter_sprint(self, sprint_id: str) -> Tuple[date, date]:
        """Parse YY.Q.# format back to date range."""
        # Pattern: YY.Q#.Sprint
        match = re.match(r"(\d{2})\.Q(\d)\.(\d+)", sprint_id)
        if not match:
            raise ValueError(f"Invalid YY.Q.# format: {sprint_id}")

        year_suffix = int(match.group(1))
        quarter = int(match.group(2))
        sprint_in_quarter = int(match.group(3))

        # Determine full year (assume 2000+ for now)
        full_year = 2000 + year_suffix

        # Calculate quarter start
        quarter_start_month = (quarter - 1) * 3 + 1
        quarter_start = date(full_year, quarter_start_month, 1)

        # Calculate sprint start within quarter
        weeks_offset = (sprint_in_quarter - 1) * self.duration_weeks
        sprint_start = quarter_start + timedelta(weeks=weeks_offset)
        sprint_end = sprint_start + timedelta(weeks=self.duration_weeks, days=-1)

        return (sprint_start, sprint_end)

    def _parse_pi_sprint(self, sprint_id: str) -> Tuple[date, date]:
        """Parse PI-N.Sprint-M format back to date range."""
        if not self.start_date:
            raise ValueError("start_date is required to parse PI-Sprint format")

        # Pattern: PI-N.Sprint-M
        match = re.match(r"PI-(\d+)\.Sprint-(\d+)", sprint_id)
        if not match:
            raise ValueError(f"Invalid PI-Sprint format: {sprint_id}")

        pi_number = int(match.group(1))
        sprint_in_pi = int(match.group(2))

        # Calculate total sprint number
        sprints_per_pi = 5
        total_sprint = ((pi_number - 1) * sprints_per_pi) + sprint_in_pi

        # Calculate date range
        weeks_offset = (total_sprint - 1) * self.duration_weeks
        sprint_start = self.start_date + timedelta(weeks=weeks_offset)
        sprint_end = sprint_start + timedelta(weeks=self.duration_weeks, days=-1)

        return (sprint_start, sprint_end)

    def _parse_calendar_week(self, sprint_id: str) -> Tuple[date, date]:
        """Parse YYYY.WW format back to date range."""
        # Pattern: YYYY.WW
        match = re.match(r"(\d{4})\.W(\d{2})", sprint_id)
        if not match:
            raise ValueError(f"Invalid YYYY.WW format: {sprint_id}")

        year = int(match.group(1))
        week = int(match.group(2))

        # Get first day of the ISO week
        # ISO week 1 is the week with the first Thursday
        jan_4 = date(year, 1, 4)
        week_1_start = jan_4 - timedelta(days=jan_4.weekday())
        sprint_start = week_1_start + timedelta(weeks=week - 1)
        sprint_end = sprint_start + timedelta(days=6)

        return (sprint_start, sprint_end)

    def get_sprint_range(
        self, start_date: date, end_date: date
    ) -> list[Tuple[str, date, date]]:
        """
        Get all sprints within a date range.

        Args:
            start_date: Range start date
            end_date: Range end date

        Returns:
            List of tuples (sprint_id, sprint_start, sprint_end)
        """
        sprints = []
        current_date = start_date

        while current_date <= end_date:
            sprint_id = self.calculate_sprint_number(current_date)
            sprint_dates = self.parse_sprint_identifier(sprint_id)

            if sprint_dates:
                sprint_start, sprint_end = sprint_dates
                if sprint_start not in [s[1] for s in sprints]:  # Avoid duplicates
                    sprints.append((sprint_id, sprint_start, sprint_end))

            # Move to next sprint period
            current_date = current_date + timedelta(weeks=self.duration_weeks)

        return sprints
