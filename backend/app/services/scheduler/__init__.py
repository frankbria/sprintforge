"""
Scheduler service module for project scheduling and Monte Carlo simulation.

This module provides:
- TaskGraph: Directed acyclic graph for task dependencies
- CPM: Critical Path Method calculations
- WorkCalendar: Holiday and weekend handling
- MonteCarloEngine: Probabilistic schedule simulation
"""

from app.services.scheduler.task_graph import TaskGraph, CycleDetectedError

__all__ = ["TaskGraph", "CycleDetectedError"]
