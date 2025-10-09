"""
Template System for Task 3.6.

Provides multiple template variations (basic/advanced), methodology-specific
templates (Agile/Waterfall), custom formula injection, and template versioning.

Supports template selection, customization, and evolution over time.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class TemplateVariation(Enum):
    """Template complexity levels."""

    BASIC = "basic"
    ADVANCED = "advanced"
    CUSTOM = "custom"


class ProjectMethodology(Enum):
    """Project management methodologies."""

    AGILE = "agile"
    WATERFALL = "waterfall"
    HYBRID = "hybrid"
    KANBAN = "kanban"


@dataclass
class TemplateMetadata:
    """Metadata for an Excel template."""

    name: str
    variation: TemplateVariation
    methodology: ProjectMethodology
    version: str
    created_at: str
    updated_at: str
    description: str
    features: Set[str] = field(default_factory=set)
    custom_formulas: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "variation": self.variation.value,
            "methodology": self.methodology.value,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "description": self.description,
            "features": list(self.features),
            "custom_formulas": self.custom_formulas,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateMetadata":
        """Create metadata from dictionary."""
        return cls(
            name=data["name"],
            variation=TemplateVariation(data["variation"]),
            methodology=ProjectMethodology(data["methodology"]),
            version=data["version"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            description=data["description"],
            features=set(data.get("features", [])),
            custom_formulas=data.get("custom_formulas", {}),
        )


@dataclass
class TemplateLayout:
    """Defines the structure and layout of a template."""

    columns: List[str]
    column_widths: Dict[str, int]
    frozen_panes: str = "A2"
    has_gantt: bool = True
    has_resource_allocation: bool = False
    has_burndown: bool = False

    # Methodology-specific features
    sprint_tracking: bool = False
    velocity_charts: bool = False
    milestone_tracking: bool = False
    phase_gates: bool = False

    def get_column_count(self) -> int:
        """Get total number of columns."""
        return len(self.columns)

    def get_column_width(self, column_name: str) -> int:
        """Get width for a specific column."""
        return self.column_widths.get(column_name, 15)


class TemplateRegistry:
    """
    Registry for managing multiple template variations.

    Provides template discovery, selection, and customization capabilities.
    """

    def __init__(self):
        """Initialize template registry."""
        self.templates: Dict[str, TemplateMetadata] = {}
        self._register_default_templates()
        logger.info("Template registry initialized")

    def _register_default_templates(self) -> None:
        """Register default template variations."""

        # Basic Agile Template
        self.register_template(TemplateMetadata(
            name="agile_basic",
            variation=TemplateVariation.BASIC,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Basic Agile template with sprint tracking",
            features={"sprints", "velocity", "burndown", "basic_gantt"},
        ))

        # Advanced Agile Template
        self.register_template(TemplateMetadata(
            name="agile_advanced",
            variation=TemplateVariation.ADVANCED,
            methodology=ProjectMethodology.AGILE,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Advanced Agile template with full metrics",
            features={
                "sprints", "velocity", "burndown", "burnup",
                "monte_carlo", "resource_allocation", "advanced_gantt",
                "critical_path", "earned_value"
            },
        ))

        # Basic Waterfall Template
        self.register_template(TemplateMetadata(
            name="waterfall_basic",
            variation=TemplateVariation.BASIC,
            methodology=ProjectMethodology.WATERFALL,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Basic Waterfall template with milestones",
            features={"milestones", "phases", "dependencies", "basic_gantt"},
        ))

        # Advanced Waterfall Template
        self.register_template(TemplateMetadata(
            name="waterfall_advanced",
            variation=TemplateVariation.ADVANCED,
            methodology=ProjectMethodology.WATERFALL,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Advanced Waterfall template with CPM and EVM",
            features={
                "milestones", "phases", "dependencies", "advanced_gantt",
                "critical_path", "earned_value", "resource_leveling",
                "monte_carlo", "phase_gates"
            },
        ))

        # Hybrid Template
        self.register_template(TemplateMetadata(
            name="hybrid",
            variation=TemplateVariation.ADVANCED,
            methodology=ProjectMethodology.HYBRID,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description="Hybrid template combining Agile and Waterfall",
            features={
                "sprints", "milestones", "velocity", "dependencies",
                "advanced_gantt", "critical_path", "burndown",
                "earned_value", "resource_allocation"
            },
        ))

        logger.info("Default templates registered", count=len(self.templates))

    def register_template(self, metadata: TemplateMetadata) -> None:
        """
        Register a new template.

        Args:
            metadata: Template metadata
        """
        self.templates[metadata.name] = metadata
        logger.debug("Template registered", name=metadata.name)

    def get_template(self, name: str) -> Optional[TemplateMetadata]:
        """
        Get template by name.

        Args:
            name: Template name

        Returns:
            TemplateMetadata if found, None otherwise
        """
        return self.templates.get(name)

    def list_templates(
        self,
        variation: Optional[TemplateVariation] = None,
        methodology: Optional[ProjectMethodology] = None,
    ) -> List[TemplateMetadata]:
        """
        List templates with optional filters.

        Args:
            variation: Filter by variation (basic/advanced/custom)
            methodology: Filter by methodology (agile/waterfall/hybrid)

        Returns:
            List of matching templates
        """
        templates = list(self.templates.values())

        if variation:
            templates = [t for t in templates if t.variation == variation]

        if methodology:
            templates = [t for t in templates if t.methodology == methodology]

        return templates

    def find_template(
        self,
        methodology: ProjectMethodology,
        variation: TemplateVariation = TemplateVariation.BASIC,
    ) -> Optional[TemplateMetadata]:
        """
        Find best matching template.

        Args:
            methodology: Desired methodology
            variation: Desired variation level

        Returns:
            Best matching template
        """
        matches = self.list_templates(
            variation=variation,
            methodology=methodology,
        )

        if matches:
            return matches[0]

        # Fallback to any template with matching methodology
        matches = self.list_templates(methodology=methodology)
        if matches:
            logger.warning(
                "Exact template not found, using fallback",
                requested_variation=variation.value,
                fallback_variation=matches[0].variation.value,
            )
            return matches[0]

        return None


class TemplateLayoutBuilder:
    """
    Builds template layouts based on methodology and features.
    """

    # Base columns common to all templates
    BASE_COLUMNS = [
        "Task ID",
        "Task Name",
        "Duration (days)",
        "Start Date",
        "End Date",
        "Status",
        "Owner",
    ]

    # Methodology-specific columns
    AGILE_COLUMNS = [
        "Sprint",
        "Story Points",
        "Velocity",
    ]

    WATERFALL_COLUMNS = [
        "Phase",
        "Milestone",
        "Dependencies",
    ]

    # Advanced feature columns
    ADVANCED_COLUMNS = [
        "Optimistic",
        "Likely",
        "Pessimistic",
        "% Complete",
        "Budget",
        "Actual Cost",
    ]

    def build_layout(
        self,
        metadata: TemplateMetadata,
    ) -> TemplateLayout:
        """
        Build template layout from metadata.

        Args:
            metadata: Template metadata

        Returns:
            TemplateLayout instance
        """
        columns = self.BASE_COLUMNS.copy()

        # Add methodology-specific columns
        if metadata.methodology == ProjectMethodology.AGILE:
            columns.extend(self.AGILE_COLUMNS)
        elif metadata.methodology == ProjectMethodology.WATERFALL:
            columns.extend(self.WATERFALL_COLUMNS)
        elif metadata.methodology == ProjectMethodology.HYBRID:
            columns.extend(self.AGILE_COLUMNS)
            columns.extend(self.WATERFALL_COLUMNS)

        # Add advanced columns if advanced variation
        if metadata.variation == TemplateVariation.ADVANCED:
            columns.extend(self.ADVANCED_COLUMNS)

        # Build column widths
        column_widths = self._calculate_column_widths(columns)

        # Determine feature flags
        layout = TemplateLayout(
            columns=columns,
            column_widths=column_widths,
            has_gantt="gantt" in metadata.features or "advanced_gantt" in metadata.features,
            has_resource_allocation="resource_allocation" in metadata.features,
            has_burndown="burndown" in metadata.features,
            sprint_tracking="sprints" in metadata.features,
            velocity_charts="velocity" in metadata.features,
            milestone_tracking="milestones" in metadata.features,
            phase_gates="phase_gates" in metadata.features,
        )

        logger.debug(
            "Layout built",
            template=metadata.name,
            columns=len(columns),
        )

        return layout

    def _calculate_column_widths(self, columns: List[str]) -> Dict[str, int]:
        """Calculate appropriate widths for columns."""
        widths = {}

        for col in columns:
            # Default widths based on column type
            if "ID" in col:
                widths[col] = 10
            elif "Name" in col or "Description" in col:
                widths[col] = 30
            elif "Date" in col:
                widths[col] = 12
            elif "%" in col or "Complete" in col:
                widths[col] = 10
            elif "Cost" in col or "Budget" in col:
                widths[col] = 12
            else:
                widths[col] = 15

        return widths


class CustomFormulaValidator:
    """
    Validates and manages custom formula injection.
    """

    # Allowed Excel functions for custom formulas
    ALLOWED_FUNCTIONS = {
        # Math & Statistics
        "SUM", "AVERAGE", "COUNT", "MIN", "MAX", "MEDIAN", "STDEV",
        # Logical
        "IF", "AND", "OR", "NOT", "IFS", "SWITCH",
        # Lookup & Reference
        "INDEX", "MATCH", "VLOOKUP", "HLOOKUP", "XLOOKUP", "OFFSET",
        # Date & Time
        "DATE", "TODAY", "NOW", "NETWORKDAYS", "WORKDAY", "EOMONTH",
        # Text
        "TEXT", "CONCATENATE", "LEFT", "RIGHT", "MID", "LEN",
        # Financial (for EVM)
        "NPV", "IRR", "PMT",
    }

    # Dangerous functions to block
    BLOCKED_FUNCTIONS = {
        "INDIRECT",  # Can access arbitrary cells
        "EVALUATE",  # Can execute arbitrary code
        "EXEC",      # Potential security risk
    }

    def validate_formula(self, formula: str) -> tuple[bool, Optional[str]]:
        """
        Validate a custom formula for security and correctness.

        Args:
            formula: Formula string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not formula:
            return False, "Formula cannot be empty"

        # Must start with =
        if not formula.startswith("="):
            return False, "Formula must start with '='"

        # Check for blocked functions
        formula_upper = formula.upper()
        for blocked in self.BLOCKED_FUNCTIONS:
            if blocked in formula_upper:
                return False, f"Blocked function detected: {blocked}"

        # Extract function names
        functions = self._extract_functions(formula)

        # Check if all functions are allowed
        unknown_functions = functions - self.ALLOWED_FUNCTIONS
        if unknown_functions:
            logger.warning(
                "Unknown functions in custom formula",
                functions=list(unknown_functions),
            )
            # Allow but warn - may be valid Excel functions we don't know about

        return True, None

    def _extract_functions(self, formula: str) -> Set[str]:
        """Extract function names from formula."""
        import re

        # Pattern to match Excel function names
        pattern = r'\b([A-Z]+)\s*\('
        matches = re.findall(pattern, formula.upper())

        return set(matches)

    def add_custom_formula(
        self,
        name: str,
        formula: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a custom formula definition.

        Args:
            name: Formula name
            formula: Formula string
            description: Human-readable description

        Returns:
            Formula definition dictionary

        Raises:
            ValueError: If formula is invalid
        """
        is_valid, error = self.validate_formula(formula)

        if not is_valid:
            raise ValueError(f"Invalid formula: {error}")

        return {
            "name": name,
            "formula": formula,
            "description": description,
            "custom": True,
            "created_at": datetime.now().isoformat(),
        }


class TemplateVersionManager:
    """
    Manages template versioning and upgrades.

    Supports semantic versioning and backward compatibility.
    """

    def __init__(self):
        """Initialize version manager."""
        self.version_history: Dict[str, List[str]] = {}
        logger.info("Template version manager initialized")

    def parse_version(self, version: str) -> tuple[int, int, int]:
        """
        Parse semantic version string.

        Args:
            version: Version string (e.g., "1.2.3")

        Returns:
            Tuple of (major, minor, patch)
        """
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")

        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            raise ValueError(f"Invalid version format: {version}")

    def compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Args:
            v1: First version
            v2: Second version

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        v1_parts = self.parse_version(v1)
        v2_parts = self.parse_version(v2)

        if v1_parts < v2_parts:
            return -1
        elif v1_parts > v2_parts:
            return 1
        else:
            return 0

    def is_compatible(self, current: str, required: str) -> bool:
        """
        Check if current version is compatible with required version.

        Compatibility rules:
        - Major version must match
        - Current minor version must be >= required minor version

        Args:
            current: Current version
            required: Required version

        Returns:
            True if compatible
        """
        curr_major, curr_minor, curr_patch = self.parse_version(current)
        req_major, req_minor, req_patch = self.parse_version(required)

        # Major version must match
        if curr_major != req_major:
            return False

        # Minor version must be >= required
        if curr_minor < req_minor:
            return False

        return True

    def increment_version(
        self,
        current: str,
        level: str = "patch",
    ) -> str:
        """
        Increment version number.

        Args:
            current: Current version
            level: Level to increment (major, minor, patch)

        Returns:
            New version string
        """
        major, minor, patch = self.parse_version(current)

        if level == "major":
            major += 1
            minor = 0
            patch = 0
        elif level == "minor":
            minor += 1
            patch = 0
        elif level == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid level: {level}")

        return f"{major}.{minor}.{patch}"

    def record_version(self, template_name: str, version: str) -> None:
        """
        Record a version in the history.

        Args:
            template_name: Template name
            version: Version string
        """
        if template_name not in self.version_history:
            self.version_history[template_name] = []

        self.version_history[template_name].append(version)

        logger.debug(
            "Version recorded",
            template=template_name,
            version=version,
        )

    def get_version_history(self, template_name: str) -> List[str]:
        """
        Get version history for a template.

        Args:
            template_name: Template name

        Returns:
            List of versions (sorted)
        """
        history = self.version_history.get(template_name, [])
        return sorted(history, key=lambda v: self.parse_version(v))


# Convenience function for template selection
def select_template(
    methodology: str,
    variation: str = "basic",
) -> Optional[TemplateMetadata]:
    """
    Select a template based on methodology and variation.

    Args:
        methodology: Project methodology (agile, waterfall, hybrid)
        variation: Template variation (basic, advanced)

    Returns:
        Selected template metadata

    Example:
        >>> template = select_template("agile", "advanced")
        >>> print(template.name)
        agile_advanced
    """
    registry = TemplateRegistry()

    try:
        method_enum = ProjectMethodology(methodology.lower())
        var_enum = TemplateVariation(variation.lower())
    except ValueError as e:
        logger.error("Invalid methodology or variation", error=str(e))
        return None

    return registry.find_template(method_enum, var_enum)
