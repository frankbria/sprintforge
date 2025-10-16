"""
CCPM Buffer Management for Critical Chain Project Management.

Implements buffer calculation, placement, consumption tracking, and status monitoring
following Goldratt's Critical Chain methodology.
"""

import math
from enum import Enum
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field


class BufferType(str, Enum):
    """Types of CCPM buffers."""

    PROJECT = "project"
    FEEDING = "feeding"


class BufferStatus(str, Enum):
    """Buffer consumption status levels."""

    GREEN = "green"  # <33% consumed
    YELLOW = "yellow"  # 33-66% consumed
    RED = "red"  # >66% consumed


class Buffer(BaseModel):
    """
    CCPM buffer data structure.

    Represents a buffer with type, size, location, and consumption tracking.

    Attributes:
        buffer_type: Type of buffer (PROJECT or FEEDING)
        size: Buffer size in working days
        location: Buffer location (task_id or 'end' for project buffer)
        consumption: Current buffer consumption in working days
    """

    buffer_type: BufferType
    size: float = Field(ge=0.0, description="Buffer size in working days")
    location: str = Field(description="Buffer location (task_id or 'end')")
    consumption: float = Field(
        default=0.0, ge=0.0, description="Current consumption in working days"
    )

    def consumption_percentage(self) -> float:
        """
        Calculate buffer consumption as percentage.

        Returns:
            Percentage of buffer consumed (0-100+)
        """
        if self.size == 0.0:
            return 0.0
        return (self.consumption / self.size) * 100.0

    def status(self) -> BufferStatus:
        """
        Determine buffer status based on consumption.

        Returns:
            BufferStatus: GREEN (<=33%), YELLOW (>33% and <=66%), or RED (>66%)
        """
        percentage = self.consumption_percentage()

        # Use <= for boundaries to handle floating point precision
        if percentage <= 33.0:
            return BufferStatus.GREEN
        elif percentage <= 66.0:
            return BufferStatus.YELLOW
        else:
            return BufferStatus.RED

    class Config:
        use_enum_values = True


class CCPMBufferCalculator:
    """
    Calculator for CCPM buffer sizing and management.

    Provides methods for:
    - Project buffer calculation (50% rule or Root Square Method)
    - Feeding buffer calculation and placement
    - Buffer consumption tracking
    - Buffer status monitoring
    """

    VALID_METHODS = {"simple", "root_square"}

    def __init__(self, method: str = "simple"):
        """
        Initialize CCPM buffer calculator.

        Args:
            method: Buffer calculation method ('simple' or 'root_square')

        Raises:
            ValueError: If method is not valid
        """
        if method not in self.VALID_METHODS:
            raise ValueError(
                f"Invalid buffer calculation method: {method}. "
                f"Must be one of {self.VALID_METHODS}"
            )
        self.method = method

    def calculate_project_buffer(
        self, critical_chain: List[str], durations: Dict[str, float]
    ) -> float:
        """
        Calculate project buffer size.

        Project buffer is placed at the end of the critical chain to protect
        the project completion date.

        Methods:
        - simple: 50% of sum of critical chain task durations
        - root_square: Root Square Method √(Σ(duration²))

        Args:
            critical_chain: List of task IDs on critical chain
            durations: Dictionary mapping task_id to duration

        Returns:
            Buffer size in working days
        """
        if not critical_chain:
            return 0.0

        if self.method == "simple":
            # Simple method: 50% of total critical chain duration
            total_duration = sum(durations[task_id] for task_id in critical_chain)
            return total_duration * 0.5

        elif self.method == "root_square":
            # Root Square Method: √(Σ(duration²))
            sum_of_squares = sum(durations[task_id] ** 2 for task_id in critical_chain)
            return math.sqrt(sum_of_squares)

        return 0.0  # Should never reach here due to validation

    def calculate_feeding_buffer(
        self, feeding_chain: List[str], durations: Dict[str, float]
    ) -> float:
        """
        Calculate feeding buffer size.

        Feeding buffer is placed where a non-critical chain joins the critical chain.
        Uses 50% of the feeding chain duration.

        Args:
            feeding_chain: List of task IDs in feeding chain
            durations: Dictionary mapping task_id to duration

        Returns:
            Buffer size in working days
        """
        if not feeding_chain:
            return 0.0

        # Feeding buffer: 50% of feeding chain duration
        total_duration = sum(durations[task_id] for task_id in feeding_chain)
        return total_duration * 0.5

    def identify_feeding_chains(
        self, graph, critical_chain: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Identify all feeding chains and their join points.

        A feeding chain is a non-critical path that merges into the critical chain.

        Args:
            graph: TaskGraph with project structure
            critical_chain: List of task IDs on critical chain

        Returns:
            List of dicts with 'chain' (task list) and 'join_point' (task_id)
        """
        feeding_chains = []
        critical_set = set(critical_chain)

        # For each task on critical chain, check for non-critical predecessors
        for critical_task in critical_chain:
            predecessors = graph.get_dependencies(critical_task)

            for pred in predecessors:
                if pred not in critical_set:
                    # Found a feeding chain - trace back to its root
                    chain = self._trace_feeding_chain(graph, pred, critical_set)
                    feeding_chains.append({"chain": chain, "join_point": critical_task})

        return feeding_chains

    def _trace_feeding_chain(
        self, graph, start_task: str, critical_set: set
    ) -> List[str]:
        """
        Trace a feeding chain backward from join point to its roots.

        Args:
            graph: TaskGraph with project structure
            start_task: Task where feeding chain joins critical chain
            critical_set: Set of task IDs on critical chain

        Returns:
            List of task IDs in feeding chain (in reverse order from root)
        """
        chain = []
        visited = set()
        stack = [start_task]

        while stack:
            task = stack.pop()

            if task in visited or task in critical_set:
                continue

            visited.add(task)
            chain.append(task)

            # Add predecessors to explore
            predecessors = graph.get_dependencies(task)
            for pred in predecessors:
                if pred not in critical_set and pred not in visited:
                    stack.append(pred)

        # Return chain in dependency order (roots first)
        return list(reversed(chain))

    def calculate_all_buffers(
        self, graph, critical_chain: List[str], durations: Dict[str, float]
    ) -> List[Buffer]:
        """
        Calculate all buffers for the project.

        Creates:
        - One project buffer at the end of critical chain
        - Feeding buffers at each join point with critical chain

        Args:
            graph: TaskGraph with project structure
            critical_chain: List of task IDs on critical chain
            durations: Dictionary mapping task_id to duration

        Returns:
            List of Buffer objects
        """
        buffers = []

        # Calculate project buffer
        project_buffer_size = self.calculate_project_buffer(critical_chain, durations)
        buffers.append(
            Buffer(
                buffer_type=BufferType.PROJECT,
                size=project_buffer_size,
                location="end",
                consumption=0.0,
            )
        )

        # Calculate feeding buffers
        feeding_chains = self.identify_feeding_chains(graph, critical_chain)

        for fc in feeding_chains:
            feeding_buffer_size = self.calculate_feeding_buffer(fc["chain"], durations)
            buffers.append(
                Buffer(
                    buffer_type=BufferType.FEEDING,
                    size=feeding_buffer_size,
                    location=fc["join_point"],
                    consumption=0.0,
                )
            )

        return buffers

    def track_buffer_consumption(self, buffer: Buffer, consumption: float) -> None:
        """
        Track buffer consumption.

        Updates buffer consumption and allows monitoring of buffer status.

        Args:
            buffer: Buffer object to update
            consumption: Additional consumption in working days
        """
        buffer.consumption += consumption

    def get_buffer_status_summary(
        self, buffers: List[Buffer]
    ) -> Dict[str, Union[int, float]]:
        """
        Generate summary of buffer statuses.

        Args:
            buffers: List of Buffer objects

        Returns:
            Dictionary with status counts and metrics
        """
        summary: Dict[str, Union[int, float]] = {
            "total_buffers": len(buffers),
            "green_count": 0,
            "yellow_count": 0,
            "red_count": 0,
            "critical_buffers": 0,
        }

        for buffer in buffers:
            status = buffer.status()
            if status == BufferStatus.GREEN:
                summary["green_count"] += 1
            elif status == BufferStatus.YELLOW:
                summary["yellow_count"] += 1
            elif status == BufferStatus.RED:
                summary["red_count"] += 1
                summary["critical_buffers"] += 1

        return summary
