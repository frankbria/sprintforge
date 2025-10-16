"""
Data models for scheduler calculations.

Contains CPM (Critical Path Method) result models with ES/EF/LS/LF fields.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class TaskScheduleData(BaseModel):
    """
    CPM calculation results for a single task.

    Attributes:
        task_id: Unique task identifier
        duration: Task duration in working days
        dependencies: List of predecessor task IDs
        es: Early Start - earliest time task can start
        ef: Early Finish - earliest time task can finish
        ls: Late Start - latest time task can start without delaying project
        lf: Late Finish - latest time task can finish without delaying project
        slack: Total slack (LS - ES) - amount of delay task can tolerate
        is_critical: True if task is on critical path (zero slack)
    """

    task_id: str
    duration: float = Field(ge=0.0, description="Task duration in working days")
    dependencies: List[str] = Field(default_factory=list)

    # CPM calculation results
    es: float = Field(default=0.0, description="Early Start")
    ef: float = Field(default=0.0, description="Early Finish")
    ls: float = Field(default=0.0, description="Late Start")
    lf: float = Field(default=0.0, description="Late Finish")
    slack: float = Field(default=0.0, description="Total Slack (LS - ES)")
    is_critical: bool = Field(default=False, description="On critical path")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "T001",
                "duration": 5.0,
                "dependencies": [],
                "es": 0.0,
                "ef": 5.0,
                "ls": 0.0,
                "lf": 5.0,
                "slack": 0.0,
                "is_critical": True,
            }
        }


class CriticalPathResult(BaseModel):
    """
    Complete CPM analysis results for a project.

    Attributes:
        tasks: Dictionary mapping task_id to TaskScheduleData
        critical_path: List of task IDs on the critical path
        project_duration: Total project duration (working days)
    """

    tasks: Dict[str, TaskScheduleData]
    critical_path: List[str] = Field(
        description="Task IDs on critical path, in order"
    )
    project_duration: float = Field(
        ge=0.0, description="Total project duration in working days"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tasks": {
                    "T001": {
                        "task_id": "T001",
                        "duration": 5.0,
                        "dependencies": [],
                        "es": 0.0,
                        "ef": 5.0,
                        "ls": 0.0,
                        "lf": 5.0,
                        "slack": 0.0,
                        "is_critical": True,
                    }
                },
                "critical_path": ["T001", "T002", "T003"],
                "project_duration": 15.0,
            }
        }
