"""
Dependency text parsing for task dependencies.

Parses comma-separated dependency strings like "T001,T002,T003" into lists
of task IDs with validation.
"""

import re
from typing import Optional, List


class DependencyParseError(Exception):
    """Raised when dependency parsing fails due to invalid format."""

    pass


def parse_dependencies(dependencies_text: Optional[str]) -> List[str]:
    """
    Parse comma-separated dependency string into list of task IDs.

    Validates task ID format and handles whitespace. Task IDs must consist
    of alphanumeric characters, underscores, and hyphens only.

    Args:
        dependencies_text: Comma-separated task IDs (e.g., "T001,T002,T003")
                          Can be None or empty string for no dependencies

    Returns:
        List of task ID strings. Empty list if input is None/empty/whitespace.

    Raises:
        DependencyParseError: If task ID format is invalid or parsing fails

    Examples:
        >>> parse_dependencies("T001,T002,T003")
        ['T001', 'T002', 'T003']

        >>> parse_dependencies("T001, T002, T003")  # spaces OK
        ['T001', 'T002', 'T003']

        >>> parse_dependencies("")
        []

        >>> parse_dependencies(None)
        []

        >>> parse_dependencies("task1")  # Invalid format
        DependencyParseError: Invalid task ID format
    """
    # Handle None, empty, or whitespace-only input
    if not dependencies_text or not dependencies_text.strip():
        return []

    # Split on commas and strip whitespace from each part
    task_ids = [task_id.strip() for task_id in dependencies_text.split(",")]

    # Validate each task ID
    # Task ID format: alphanumeric, underscore, hyphen only (at least 1 character)
    task_id_pattern = re.compile(r"^[A-Za-z0-9_-]+$")

    result = []
    for task_id in task_ids:
        # Check for empty task IDs (from trailing/leading/double commas)
        if not task_id:
            raise DependencyParseError(
                f"Empty task ID found in dependencies: '{dependencies_text}'"
            )

        # Validate format
        if not task_id_pattern.match(task_id):
            raise DependencyParseError(
                f"Invalid task ID format: '{task_id}'. "
                f"Task IDs must contain only letters, numbers, underscores, and hyphens."
            )

        result.append(task_id)

    return result
