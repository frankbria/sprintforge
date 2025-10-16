"""
TaskGraph data structure for managing task dependencies.

Implements a directed acyclic graph (DAG) using adjacency lists.
Provides topological sorting and cycle detection for project scheduling.
"""

from typing import Dict, List, Any, Set
from collections import defaultdict, deque


class CycleDetectedError(Exception):
    """Raised when a circular dependency is detected in the task graph."""
    pass


class TaskGraph:
    """
    Directed acyclic graph for task dependencies.

    Uses adjacency list representation for efficient dependency tracking.
    Supports topological sorting and cycle detection.

    Attributes:
        nodes: Dict mapping task_id to task metadata
        _edges: Dict mapping task_id to list of successor task_ids
        _reverse_edges: Dict mapping task_id to list of predecessor task_ids
    """

    def __init__(self):
        """Initialize empty task graph."""
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: Dict[str, List[str]] = defaultdict(list)
        self._reverse_edges: Dict[str, List[str]] = defaultdict(list)

    def add_node(self, task_id: str, **task_data) -> None:
        """
        Add a task node to the graph.

        Args:
            task_id: Unique identifier for the task
            **task_data: Arbitrary task metadata (duration, name, owner, etc.)

        Raises:
            ValueError: If task_id already exists
        """
        if task_id in self.nodes:
            raise ValueError(f"Task {task_id} already exists in graph")

        self.nodes[task_id] = task_data

    def add_edge(self, from_task: str, to_task: str) -> None:
        """
        Add a dependency edge from one task to another.

        Creates a directed edge: from_task → to_task
        Meaning: to_task depends on from_task (from_task must complete first)

        Args:
            from_task: Predecessor task ID
            to_task: Successor task ID (depends on from_task)

        Raises:
            ValueError: If either task doesn't exist or edge would create self-reference
        """
        # Validate tasks exist
        if from_task not in self.nodes:
            raise ValueError(f"Task {from_task} not found in graph")
        if to_task not in self.nodes:
            raise ValueError(f"Task {to_task} not found in graph")

        # Prevent self-referencing edges
        if from_task == to_task:
            raise ValueError(f"Cannot create self-referencing edge for task {from_task}")

        # Add edge (idempotent - duplicate edges ignored)
        if to_task not in self._edges[from_task]:
            self._edges[from_task].append(to_task)
            self._reverse_edges[to_task].append(from_task)

    def get_dependencies(self, task_id: str) -> List[str]:
        """
        Get list of tasks that this task depends on (predecessors).

        Args:
            task_id: Task to get dependencies for

        Returns:
            List of predecessor task IDs

        Raises:
            ValueError: If task doesn't exist
        """
        if task_id not in self.nodes:
            raise ValueError(f"Task {task_id} not found in graph")

        return self._reverse_edges.get(task_id, [])

    def get_successors(self, task_id: str) -> List[str]:
        """
        Get list of tasks that depend on this task (successors).

        Args:
            task_id: Task to get successors for

        Returns:
            List of successor task IDs

        Raises:
            ValueError: If task doesn't exist
        """
        if task_id not in self.nodes:
            raise ValueError(f"Task {task_id} not found in graph")

        return self._edges.get(task_id, [])

    def has_dependencies(self, task_id: str) -> bool:
        """
        Check if task has any dependencies.

        Args:
            task_id: Task to check

        Returns:
            True if task has dependencies, False otherwise

        Raises:
            ValueError: If task doesn't exist
        """
        if task_id not in self.nodes:
            raise ValueError(f"Task {task_id} not found in graph")

        return len(self._reverse_edges.get(task_id, [])) > 0

    def is_empty(self) -> bool:
        """
        Check if graph has no nodes.

        Returns:
            True if graph is empty, False otherwise
        """
        return len(self.nodes) == 0

    def topological_sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.

        Returns tasks in dependency order: predecessors before successors.
        Detects cycles during sorting.

        Returns:
            List of task IDs in topological order

        Raises:
            CycleDetectedError: If graph contains a cycle
        """
        # Calculate in-degrees for all nodes
        in_degree = {task_id: 0 for task_id in self.nodes}
        for task_id in self.nodes:
            for successor in self._edges.get(task_id, []):
                in_degree[successor] += 1

        # Initialize queue with nodes that have no dependencies
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            # Process node with no remaining dependencies
            task_id = queue.popleft()
            result.append(task_id)

            # Reduce in-degree for all successors
            for successor in self._edges.get(task_id, []):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        # If not all nodes processed, there's a cycle
        if len(result) != len(self.nodes):
            # Find nodes involved in cycle
            remaining = set(self.nodes.keys()) - set(result)
            raise CycleDetectedError(
                f"Circular dependency detected involving tasks: {', '.join(sorted(remaining))}"
            )

        return result

    def __repr__(self) -> str:
        """String representation of graph."""
        return f"TaskGraph(nodes={len(self.nodes)}, edges={sum(len(v) for v in self._edges.values())})"
