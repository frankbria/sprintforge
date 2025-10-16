"""
Tests for SchedulerService - complete schedule calculation integration.

Tests the orchestration of TaskGraph, CPM, WorkCalendar, and dependency parsing
to provide end-to-end project scheduling functionality.
"""

import pytest
from datetime import date
from app.services.scheduler.scheduler_service import (
    SchedulerService,
    SchedulerError,
    TaskInput,
    ScheduleResult,
)


class TestSchedulerServiceBasics:
    """Test basic SchedulerService functionality."""

    def test_single_task_schedule(self):
        """Test scheduling single task with no dependencies."""
        tasks = [
            TaskInput(task_id="T001", duration=5.0, dependencies="")
        ]

        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 13),  # Monday
        )

        assert result.project_duration == 5.0
        assert len(result.tasks) == 1
        assert result.tasks["T001"].task_id == "T001"
        assert result.tasks["T001"].is_critical is True
        assert result.critical_path == ["T001"]

        # Check calendar dates
        assert result.task_dates["T001"] == (date(2025, 1, 13), date(2025, 1, 17))

    def test_simple_sequence_schedule(self):
        """Test scheduling simple task sequence."""
        tasks = [
            TaskInput(task_id="T001", duration=3.0, dependencies=""),
            TaskInput(task_id="T002", duration=5.0, dependencies="T001"),
        ]

        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 13),  # Monday
        )

        assert result.project_duration == 8.0
        assert len(result.tasks) == 2
        assert result.critical_path == ["T001", "T002"]

        # T001: Mon-Wed (3 days)
        # T002: starts after T001, 5 days
        assert result.task_dates["T001"][0] == date(2025, 1, 13)
        assert result.task_dates["T002"][1] == date(2025, 1, 22)  # Thursday next week

    def test_parallel_tasks_schedule(self):
        """Test scheduling parallel tasks."""
        tasks = [
            TaskInput(task_id="T001", duration=5.0, dependencies=""),
            TaskInput(task_id="T002", duration=3.0, dependencies="T001"),
            TaskInput(task_id="T003", duration=7.0, dependencies="T001"),
        ]

        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 13),  # Monday
        )

        # T003 (duration 7) is longer than T002 (duration 3), so it's on critical path
        assert result.project_duration == 12.0
        assert "T003" in result.critical_path
        assert "T001" in result.critical_path

    def test_multiple_dependencies_schedule(self):
        """Test task with multiple dependencies."""
        tasks = [
            TaskInput(task_id="T001", duration=3.0, dependencies=""),
            TaskInput(task_id="T002", duration=5.0, dependencies=""),
            TaskInput(task_id="T003", duration=2.0, dependencies="T001,T002"),
        ]

        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 13),
        )

        # T003 starts after both T001 and T002 finish
        # T002 (5 days) takes longer, so T003 starts after T002
        assert result.tasks["T003"].es == 5.0
        assert result.project_duration == 7.0


class TestSchedulerServiceCalendar:
    """Test calendar integration."""

    def test_schedule_with_weekends(self):
        """Test schedule calculation skipping weekends."""
        tasks = [
            TaskInput(task_id="T001", duration=3.0, dependencies=""),
        ]

        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 16),  # Thursday
        )

        # 3 working days: Thu, Fri, Mon (skip weekend)
        assert result.task_dates["T001"] == (date(2025, 1, 16), date(2025, 1, 20))

    def test_schedule_with_holidays(self):
        """Test schedule calculation with holidays."""
        tasks = [
            TaskInput(task_id="T001", duration=5.0, dependencies=""),
        ]

        holidays = [date(2025, 1, 15)]  # Wednesday
        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 13),  # Monday
            holidays=holidays,
        )

        # 5 working days, skipping Wed holiday: Mon, Tue, Thu, Fri, Mon
        assert result.task_dates["T001"] == (date(2025, 1, 13), date(2025, 1, 20))

    def test_schedule_with_custom_workdays(self):
        """Test schedule with custom workday configuration."""
        tasks = [
            TaskInput(task_id="T001", duration=5.0, dependencies=""),
        ]

        # Sunday-Thursday workweek (Middle East schedule)
        workdays = {6, 0, 1, 2, 3}  # Sun-Thu
        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 19),  # Sunday
            workdays=workdays,
        )

        # 5 working days: Sun-Thu
        assert result.task_dates["T001"] == (date(2025, 1, 19), date(2025, 1, 23))


class TestSchedulerServiceValidation:
    """Test validation and error handling."""

    def test_reject_nonexistent_dependency(self):
        """Test rejection of dependency on nonexistent task."""
        tasks = [
            TaskInput(task_id="T001", duration=3.0, dependencies="T999"),
        ]

        scheduler = SchedulerService()
        with pytest.raises(SchedulerError, match="Unknown dependency"):
            scheduler.calculate_schedule(
                tasks=tasks,
                project_start=date(2025, 1, 13),
            )

    def test_reject_circular_dependency(self):
        """Test rejection of circular dependencies."""
        tasks = [
            TaskInput(task_id="T001", duration=3.0, dependencies="T002"),
            TaskInput(task_id="T002", duration=5.0, dependencies="T001"),
        ]

        scheduler = SchedulerService()
        with pytest.raises(SchedulerError, match="Circular dependency|cycle"):
            scheduler.calculate_schedule(
                tasks=tasks,
                project_start=date(2025, 1, 13),
            )

    def test_reject_duplicate_task_ids(self):
        """Test rejection of duplicate task IDs."""
        tasks = [
            TaskInput(task_id="T001", duration=3.0, dependencies=""),
            TaskInput(task_id="T001", duration=5.0, dependencies=""),
        ]

        scheduler = SchedulerService()
        with pytest.raises(SchedulerError, match="Duplicate task ID"):
            scheduler.calculate_schedule(
                tasks=tasks,
                project_start=date(2025, 1, 13),
            )

    def test_reject_negative_duration(self):
        """Test rejection of negative duration."""
        # Pydantic validates duration > 0, so ValidationError is raised at model creation
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError, match="greater than"):
            TaskInput(task_id="T001", duration=-3.0, dependencies="")

    def test_reject_zero_duration(self):
        """Test rejection of zero duration."""
        # Pydantic validates duration > 0, so ValidationError is raised at model creation
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError, match="greater than"):
            TaskInput(task_id="T001", duration=0.0, dependencies="")


class TestSchedulerServiceFractional:
    """Test fractional duration support."""

    def test_fractional_duration_task(self):
        """Test task with fractional duration."""
        tasks = [
            TaskInput(task_id="T001", duration=2.5, dependencies=""),
        ]

        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 13),  # Monday
        )

        assert result.tasks["T001"].duration == 2.5
        assert result.project_duration == 2.5


class TestSchedulerServiceRealistic:
    """Test realistic project scenarios."""

    def test_software_project_schedule(self):
        """Test realistic software project schedule."""
        tasks = [
            # Design phase
            TaskInput(task_id="DESIGN_001", duration=5.0, dependencies=""),

            # Development phase (depends on design)
            TaskInput(task_id="DEV_001", duration=10.0, dependencies="DESIGN_001"),
            TaskInput(task_id="DEV_002", duration=8.0, dependencies="DESIGN_001"),

            # Testing phase (depends on development)
            TaskInput(task_id="TEST_001", duration=5.0, dependencies="DEV_001,DEV_002"),

            # Deployment (depends on testing)
            TaskInput(task_id="DEPLOY_001", duration=2.0, dependencies="TEST_001"),
        ]

        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 13),  # Monday
        )

        # Design: 5 days
        # Dev (parallel, max 10 days): 10 days
        # Test: 5 days
        # Deploy: 2 days
        # Total: 5 + 10 + 5 + 2 = 22 working days
        assert result.project_duration == 22.0

        # Critical path should go through longest development task
        assert "DEV_001" in result.critical_path
        assert "DEPLOY_001" in result.critical_path

    def test_empty_task_list(self):
        """Test handling empty task list."""
        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=[],
            project_start=date(2025, 1, 13),
        )

        assert result.project_duration == 0.0
        assert len(result.tasks) == 0
        assert len(result.critical_path) == 0
        assert len(result.task_dates) == 0

    def test_large_project_schedule(self):
        """Test large project with many tasks."""
        # Create 50 tasks with various dependencies
        tasks = []
        for i in range(1, 51):
            task_id = f"T{i:03d}"
            duration = float((i % 7) + 1)  # 1-7 days

            # Create some dependencies
            deps = []
            if i > 1 and i % 3 == 0:
                deps.append(f"T{i-1:03d}")
            if i > 2 and i % 5 == 0:
                deps.append(f"T{i-2:03d}")

            tasks.append(TaskInput(
                task_id=task_id,
                duration=duration,
                dependencies=",".join(deps)
            ))

        scheduler = SchedulerService()
        result = scheduler.calculate_schedule(
            tasks=tasks,
            project_start=date(2025, 1, 13),
        )

        # Should complete without errors
        assert result.project_duration > 0
        assert len(result.tasks) == 50
        assert len(result.critical_path) > 0
