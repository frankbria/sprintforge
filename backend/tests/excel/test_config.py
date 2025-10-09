"""Tests for project configuration models."""

import pytest
from datetime import date
from pydantic import ValidationError

from app.excel.config import (
    ProjectConfig,
    SprintConfig,
    WorkingDaysConfig,
    ProjectFeatures,
    SprintPatternType,
    FeatureFlag,
)


class TestWorkingDaysConfig:
    """Test working days and holidays configuration."""

    def test_default_working_days(self):
        """Test default working days configuration."""
        config = WorkingDaysConfig()

        assert config.working_days == [1, 2, 3, 4, 5]  # Monday-Friday
        assert config.holidays == []
        assert config.hours_per_day == 8.0

    def test_custom_working_days(self):
        """Test custom working days configuration."""
        config = WorkingDaysConfig(
            working_days=[1, 2, 3, 4],  # Monday-Thursday
            hours_per_day=6.0
        )

        assert config.working_days == [1, 2, 3, 4]
        assert config.hours_per_day == 6.0

    def test_working_days_sorted(self):
        """Test working days are automatically sorted."""
        config = WorkingDaysConfig(working_days=[5, 1, 3, 2, 4])

        assert config.working_days == [1, 2, 3, 4, 5]

    def test_invalid_working_day_number(self):
        """Test validation fails for invalid weekday numbers."""
        with pytest.raises(ValidationError) as exc_info:
            WorkingDaysConfig(working_days=[1, 2, 8])  # 8 is invalid

        assert "Invalid weekday number" in str(exc_info.value)

    def test_duplicate_working_days(self):
        """Test validation fails for duplicate days."""
        with pytest.raises(ValidationError) as exc_info:
            WorkingDaysConfig(working_days=[1, 2, 2, 3])

        assert "Duplicate working days" in str(exc_info.value)

    def test_empty_working_days(self):
        """Test validation fails for empty working days."""
        with pytest.raises(ValidationError) as exc_info:
            WorkingDaysConfig(working_days=[])

        assert "At least one working day" in str(exc_info.value)

    def test_holidays_configuration(self):
        """Test holidays configuration."""
        holidays = [
            date(2025, 1, 1),  # New Year
            date(2025, 7, 4),  # Independence Day
            date(2025, 12, 25),  # Christmas
        ]
        config = WorkingDaysConfig(holidays=holidays)

        assert len(config.holidays) == 3
        assert config.holidays[0] == date(2025, 1, 1)

    def test_holidays_sorted_and_deduplicated(self):
        """Test holidays are sorted and duplicates removed."""
        holidays = [
            date(2025, 12, 25),
            date(2025, 1, 1),
            date(2025, 7, 4),
            date(2025, 1, 1),  # Duplicate
        ]
        config = WorkingDaysConfig(holidays=holidays)

        assert len(config.holidays) == 3  # Duplicate removed
        assert config.holidays == [
            date(2025, 1, 1),
            date(2025, 7, 4),
            date(2025, 12, 25),
        ]

    def test_hours_per_day_validation(self):
        """Test hours per day validation."""
        # Valid range
        config = WorkingDaysConfig(hours_per_day=8.5)
        assert config.hours_per_day == 8.5

        # Below minimum
        with pytest.raises(ValidationError):
            WorkingDaysConfig(hours_per_day=0.5)

        # Above maximum
        with pytest.raises(ValidationError):
            WorkingDaysConfig(hours_per_day=25.0)


class TestSprintConfig:
    """Test sprint configuration."""

    def test_default_sprint_config(self):
        """Test default sprint configuration."""
        config = SprintConfig()

        assert config.pattern_type == SprintPatternType.YEAR_QUARTER_NUMBER
        assert config.duration_weeks == 2
        assert config.start_date is None
        assert config.custom_pattern is None

    def test_year_quarter_pattern(self):
        """Test Year.Quarter.# pattern configuration."""
        config = SprintConfig(
            pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
            duration_weeks=2
        )

        assert config.pattern_type == SprintPatternType.YEAR_QUARTER_NUMBER

    def test_pi_sprint_pattern(self):
        """Test PI-N.Sprint-M pattern configuration."""
        config = SprintConfig(
            pattern_type=SprintPatternType.PI_SPRINT,
            duration_weeks=2,
            start_date=date(2025, 1, 1)
        )

        assert config.pattern_type == SprintPatternType.PI_SPRINT
        assert config.start_date == date(2025, 1, 1)

    def test_calendar_week_pattern(self):
        """Test YYYY.WW pattern configuration."""
        config = SprintConfig(
            pattern_type=SprintPatternType.CALENDAR_WEEK,
            duration_weeks=1
        )

        assert config.pattern_type == SprintPatternType.CALENDAR_WEEK

    def test_custom_pattern_validation(self):
        """Test custom pattern requires custom_pattern string."""
        # Should fail without custom_pattern
        with pytest.raises(ValidationError) as exc_info:
            SprintConfig(pattern_type=SprintPatternType.CUSTOM)

        assert "custom_pattern must be provided" in str(exc_info.value)

        # Should succeed with custom_pattern
        config = SprintConfig(
            pattern_type=SprintPatternType.CUSTOM,
            custom_pattern="{YYYY}.Sprint-{#}"
        )
        assert config.custom_pattern == "{YYYY}.Sprint-{#}"

    def test_duration_weeks_validation(self):
        """Test sprint duration validation."""
        # Valid range
        config = SprintConfig(duration_weeks=3)
        assert config.duration_weeks == 3

        # Below minimum
        with pytest.raises(ValidationError):
            SprintConfig(duration_weeks=0)

        # Above maximum
        with pytest.raises(ValidationError):
            SprintConfig(duration_weeks=9)


class TestProjectFeatures:
    """Test project features and feature flags."""

    def test_default_features(self):
        """Test default feature configuration."""
        features = ProjectFeatures()

        assert features.critical_path is True
        assert features.earned_value is True
        assert features.burndown_charts is True
        assert features.monte_carlo is False
        assert features.resource_leveling is False
        assert features.baseline_tracking is False
        assert features.custom_formulas is False

    def test_custom_features(self):
        """Test custom feature configuration."""
        features = ProjectFeatures(
            monte_carlo=True,
            resource_leveling=True,
            critical_path=False
        )

        assert features.monte_carlo is True
        assert features.resource_leveling is True
        assert features.critical_path is False

    def test_get_enabled_features(self):
        """Test getting list of enabled features."""
        features = ProjectFeatures(
            critical_path=True,
            earned_value=True,
            monte_carlo=False
        )

        enabled = features.get_enabled_features()

        assert "critical_path" in enabled
        assert "earned_value" in enabled
        assert "burndown_charts" in enabled
        assert "monte_carlo" not in enabled
        assert "resource_leveling" not in enabled

    def test_is_enabled_method(self):
        """Test checking if specific feature is enabled."""
        features = ProjectFeatures(monte_carlo=True, critical_path=False)

        assert features.is_enabled(FeatureFlag.MONTE_CARLO) is True
        assert features.is_enabled(FeatureFlag.CRITICAL_PATH) is False
        assert features.is_enabled(FeatureFlag.EARNED_VALUE) is True  # Default


class TestProjectConfig:
    """Test complete project configuration."""

    def test_minimal_project_config(self):
        """Test minimal required project configuration."""
        config = ProjectConfig(
            project_id="test_proj",
            project_name="Test Project"
        )

        assert config.project_id == "test_proj"
        assert config.project_name == "Test Project"
        assert config.sprint_config.pattern_type == SprintPatternType.YEAR_QUARTER_NUMBER
        assert config.working_days_config.working_days == [1, 2, 3, 4, 5]
        assert config.features.critical_path is True

    def test_complete_project_config(self):
        """Test complete project configuration with all options."""
        config = ProjectConfig(
            project_id="proj_2025_q1",
            project_name="Q1 2025 Initiative",
            sprint_config=SprintConfig(
                pattern_type=SprintPatternType.PI_SPRINT,
                duration_weeks=2,
                start_date=date(2025, 1, 6)
            ),
            working_days_config=WorkingDaysConfig(
                working_days=[1, 2, 3, 4, 5],
                holidays=[date(2025, 1, 1), date(2025, 7, 4)],
                hours_per_day=8.0
            ),
            features=ProjectFeatures(
                monte_carlo=True,
                critical_path=True,
                earned_value=True
            ),
            metadata={"department": "Engineering", "cost_center": "CC-123"}
        )

        assert config.project_id == "proj_2025_q1"
        assert config.sprint_config.pattern_type == SprintPatternType.PI_SPRINT
        assert config.working_days_config.hours_per_day == 8.0
        assert config.features.monte_carlo is True
        assert config.metadata["department"] == "Engineering"

    def test_project_id_validation(self):
        """Test project ID validation."""
        # Valid IDs
        config1 = ProjectConfig(project_id="project-123", project_name="Test")
        assert config1.project_id == "project-123"

        config2 = ProjectConfig(project_id="proj_abc_123", project_name="Test")
        assert config2.project_id == "proj_abc_123"

        # Invalid characters
        with pytest.raises(ValidationError):
            ProjectConfig(project_id="project#123", project_name="Test")

        # Too short
        with pytest.raises(ValidationError):
            ProjectConfig(project_id="", project_name="Test")

    def test_project_name_validation(self):
        """Test project name validation."""
        # Valid name
        config = ProjectConfig(
            project_id="proj_1",
            project_name="My Project 2025 - Q1"
        )
        assert config.project_name == "My Project 2025 - Q1"

        # Too short
        with pytest.raises(ValidationError):
            ProjectConfig(project_id="proj_1", project_name="")

    def test_get_sprint_pattern(self):
        """Test getting sprint pattern string."""
        # Standard pattern
        config1 = ProjectConfig(
            project_id="p1",
            project_name="Test",
            sprint_config=SprintConfig(pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER)
        )
        assert config1.get_sprint_pattern() == "YY.Q.#"

        # Custom pattern
        config2 = ProjectConfig(
            project_id="p2",
            project_name="Test",
            sprint_config=SprintConfig(
                pattern_type=SprintPatternType.CUSTOM,
                custom_pattern="Sprint-{#}"
            )
        )
        assert config2.get_sprint_pattern() == "Sprint-{#}"

    def test_get_working_days_list(self):
        """Test getting working days list."""
        config = ProjectConfig(
            project_id="p1",
            project_name="Test",
            working_days_config=WorkingDaysConfig(working_days=[1, 2, 3])
        )

        assert config.get_working_days_list() == [1, 2, 3]

    def test_get_holidays_list(self):
        """Test getting holidays list."""
        holidays = [date(2025, 1, 1), date(2025, 7, 4)]
        config = ProjectConfig(
            project_id="p1",
            project_name="Test",
            working_days_config=WorkingDaysConfig(holidays=holidays)
        )

        assert config.get_holidays_list() == holidays

    def test_to_legacy_dict(self):
        """Test conversion to legacy dictionary format."""
        config = ProjectConfig(
            project_id="proj_1",
            project_name="Test Project",
            sprint_config=SprintConfig(duration_weeks=2),
            working_days_config=WorkingDaysConfig(
                holidays=[date(2025, 1, 1)]
            ),
            metadata={"key": "value"}
        )

        legacy_dict = config.to_legacy_dict()

        assert legacy_dict["project_id"] == "proj_1"
        assert legacy_dict["project_name"] == "Test Project"
        assert legacy_dict["sprint_pattern"] == "YY.Q.#"
        assert legacy_dict["working_days"] == [1, 2, 3, 4, 5]
        assert legacy_dict["holidays"] == ["2025-01-01"]
        assert legacy_dict["sprint_duration_weeks"] == 2
        assert legacy_dict["metadata"] == {"key": "value"}

    def test_configuration_immutability(self):
        """Test that configuration can be updated."""
        config = ProjectConfig(
            project_id="proj_1",
            project_name="Test Project"
        )

        # Pydantic models are mutable by default
        # But we can create new instances with model_copy
        new_config = config.model_copy(update={"project_name": "Updated Project"})
        assert new_config.project_name == "Updated Project"
        assert config.project_name == "Test Project"  # Original unchanged


class TestProjectConfigExamples:
    """Test realistic project configuration examples."""

    def test_agile_scrum_configuration(self):
        """Test typical Agile/Scrum project configuration."""
        config = ProjectConfig(
            project_id="scrum_2025",
            project_name="Scrum Team Alpha - 2025",
            sprint_config=SprintConfig(
                pattern_type=SprintPatternType.YEAR_QUARTER_NUMBER,
                duration_weeks=2
            ),
            working_days_config=WorkingDaysConfig(
                working_days=[1, 2, 3, 4, 5],
                hours_per_day=8.0
            ),
            features=ProjectFeatures(
                burndown_charts=True,
                critical_path=False,  # Not typically used in Scrum
                monte_carlo=False
            )
        )

        assert config.features.burndown_charts is True
        assert config.sprint_config.duration_weeks == 2

    def test_safe_pi_configuration(self):
        """Test SAFe Program Increment configuration."""
        config = ProjectConfig(
            project_id="safe_art_1",
            project_name="ART 1 - Program Increment 2025.1",
            sprint_config=SprintConfig(
                pattern_type=SprintPatternType.PI_SPRINT,
                duration_weeks=2,
                start_date=date(2025, 1, 6)  # PI start date
            ),
            features=ProjectFeatures(
                critical_path=True,
                earned_value=True,
                baseline_tracking=True
            )
        )

        assert config.sprint_config.pattern_type == SprintPatternType.PI_SPRINT
        assert config.features.baseline_tracking is True

    def test_waterfall_project_configuration(self):
        """Test waterfall project configuration."""
        config = ProjectConfig(
            project_id="waterfall_2025",
            project_name="Enterprise System Upgrade",
            sprint_config=SprintConfig(
                pattern_type=SprintPatternType.CALENDAR_WEEK,
                duration_weeks=1  # Track by week
            ),
            features=ProjectFeatures(
                critical_path=True,
                earned_value=True,
                monte_carlo=True,
                burndown_charts=False  # Not used in waterfall
            )
        )

        assert config.features.critical_path is True
        assert config.features.monte_carlo is True
        assert config.features.burndown_charts is False
