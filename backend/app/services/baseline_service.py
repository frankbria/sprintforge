"""
BaselineService - Business logic layer for baseline management and comparison.

Handles creation of project snapshots, baseline activation, and variance analysis
between current project state and historical baselines.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
import json

from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.baseline import ProjectBaseline
from app.models.project import Project


class BaselineError(Exception):
    """Raised when baseline operations fail."""

    pass


class BaselineService:
    """
    Business logic service for project baseline management.

    Handles:
    - Creating immutable snapshots of project state
    - Managing active baseline status
    - Computing variance between baseline and current state
    - Caching comparison results
    """

    MAX_SNAPSHOT_SIZE = 10 * 1024 * 1024  # 10MB in bytes

    async def create_baseline(
        self,
        project_id: UUID,
        name: str,
        description: Optional[str],
        db: AsyncSession,
    ) -> ProjectBaseline:
        """
        Create a new baseline snapshot for a project.

        Uses SERIALIZABLE transaction isolation to ensure snapshot consistency.

        Args:
            project_id: Project UUID
            name: Baseline name
            description: Optional baseline description
            db: Database session

        Returns:
            Created ProjectBaseline instance

        Raises:
            BaselineError: If snapshot creation fails
            ValueError: If snapshot exceeds size limit
        """
        try:
            # Start SERIALIZABLE transaction for consistent snapshot
            async with db.begin_nested():
                # Set transaction isolation level
                await db.execute(
                    text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                )

                # Build snapshot data
                snapshot_data = await self._build_snapshot_data(project_id, db)

                # Validate snapshot size
                snapshot_json = json.dumps(snapshot_data)
                snapshot_size = len(snapshot_json.encode("utf-8"))

                if snapshot_size > self.MAX_SNAPSHOT_SIZE:
                    raise ValueError(
                        f"Snapshot size ({snapshot_size} bytes) exceeds maximum "
                        f"allowed size ({self.MAX_SNAPSHOT_SIZE} bytes)"
                    )

                # Create baseline
                baseline = ProjectBaseline(
                    project_id=project_id,
                    name=name,
                    description=description,
                    snapshot_data=snapshot_data,
                    is_active=False,
                    snapshot_size_bytes=snapshot_size,
                )

                db.add(baseline)
                await db.flush()  # Flush to get ID without committing

            # Commit the transaction
            await db.commit()

            # Refresh to get all computed fields
            await db.refresh(baseline)

            return baseline

        except IntegrityError as e:
            await db.rollback()
            raise BaselineError(f"Failed to create baseline: {e}") from e
        except Exception as e:
            await db.rollback()
            raise BaselineError(f"Snapshot creation failed: {e}") from e

    async def set_baseline_active(
        self,
        baseline_id: UUID,
        project_id: UUID,
        db: AsyncSession,
    ) -> ProjectBaseline:
        """
        Set a baseline as active and deactivate all others for the project.

        Uses a transaction to ensure atomic operation (no race conditions).

        Args:
            baseline_id: Baseline UUID to activate
            project_id: Project UUID
            db: Database session

        Returns:
            Updated ProjectBaseline instance

        Raises:
            BaselineError: If baseline not found or update fails
        """
        try:
            async with db.begin_nested():
                # Deactivate all baselines for this project
                await db.execute(
                    update(ProjectBaseline)
                    .where(ProjectBaseline.project_id == project_id)
                    .values(is_active=False)
                )

                # Activate the selected baseline
                result = await db.execute(
                    update(ProjectBaseline)
                    .where(ProjectBaseline.id == baseline_id)
                    .values(is_active=True)
                    .returning(ProjectBaseline)
                )

                baseline = result.scalar_one_or_none()

                if not baseline:
                    raise BaselineError(
                        f"Baseline {baseline_id} not found or does not belong to project {project_id}"
                    )

            await db.commit()
            await db.refresh(baseline)

            return baseline

        except Exception as e:
            await db.rollback()
            raise BaselineError(f"Failed to activate baseline: {e}") from e

    async def compare_to_baseline(
        self,
        baseline_id: UUID,
        project_id: UUID,
        db: AsyncSession,
        include_unchanged: bool = False,
    ) -> Dict[str, Any]:
        """
        Compare current project state against a baseline.

        Calculates task-level variances, identifies new/deleted tasks,
        and provides summary statistics.

        Args:
            baseline_id: Baseline UUID to compare against
            project_id: Project UUID
            db: Database session
            include_unchanged: Include tasks with zero variance

        Returns:
            Dictionary with comparison results

        Raises:
            BaselineError: If baseline not found or comparison fails
        """
        try:
            # Get baseline
            result = await db.execute(
                select(ProjectBaseline).where(ProjectBaseline.id == baseline_id)
            )
            baseline = result.scalar_one_or_none()

            if not baseline or baseline.project_id != project_id:
                raise BaselineError(
                    f"Baseline {baseline_id} not found or does not belong to project {project_id}"
                )

            # Get current project state
            current_snapshot = await self._build_snapshot_data(project_id, db)

            # Perform variance analysis
            comparison = self._calculate_variance(
                baseline.snapshot_data,
                current_snapshot,
                include_unchanged=include_unchanged,
            )

            # Add baseline metadata
            comparison["baseline"] = {
                "id": str(baseline.id),
                "name": baseline.name,
                "created_at": baseline.created_at.isoformat(),
            }
            comparison["comparison_date"] = datetime.utcnow().isoformat()

            return comparison

        except BaselineError:
            raise
        except Exception as e:
            raise BaselineError(f"Comparison failed: {e}") from e

    async def _build_snapshot_data(
        self, project_id: UUID, db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Build complete snapshot data for a project.

        Captures all project metadata, tasks, and calculated values
        needed for future comparison.

        Args:
            project_id: Project UUID
            db: Database session

        Returns:
            Dictionary with complete project snapshot

        Raises:
            BaselineError: If project not found
        """
        # Get project
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise BaselineError(f"Project {project_id} not found")

        # For MVP, we're capturing basic project metadata
        # In production, this would include:
        # - All tasks with dependencies, dates, status
        # - Critical path calculation
        # - Monte Carlo results
        # - Resource assignments

        snapshot = {
            "project": {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "configuration": project.configuration,
                "template_version": project.template_version,
            },
            "tasks": [],  # TODO: Implement task retrieval
            "critical_path": [],  # TODO: Implement critical path calculation
            "monte_carlo_results": {},  # TODO: Implement MC results retrieval
            "snapshot_metadata": {
                "total_tasks": 0,  # TODO: Calculate from actual tasks
                "completion_pct": 0.0,  # TODO: Calculate from task statuses
                "snapshot_timestamp": datetime.utcnow().isoformat(),
            },
        }

        return snapshot

    def _calculate_variance(
        self,
        baseline_snapshot: Dict[str, Any],
        current_snapshot: Dict[str, Any],
        include_unchanged: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculate variance between baseline and current state.

        Args:
            baseline_snapshot: Historical baseline snapshot data
            current_snapshot: Current project state
            include_unchanged: Whether to include tasks with zero variance

        Returns:
            Dictionary with variance analysis
        """
        # Build task lookup dictionaries
        baseline_tasks = {
            t["id"]: t for t in baseline_snapshot.get("tasks", [])
        }
        current_tasks = {
            t["id"]: t for t in current_snapshot.get("tasks", [])
        }

        # Calculate task variances
        task_variances = []
        for task_id, baseline_task in baseline_tasks.items():
            if task_id in current_tasks:
                current_task = current_tasks[task_id]
                variance = self._calculate_task_variance(baseline_task, current_task)

                # Filter unchanged tasks if requested
                if include_unchanged or variance["variance_days"] != 0:
                    task_variances.append(variance)

        # Find new and deleted tasks
        new_task_ids = set(current_tasks.keys()) - set(baseline_tasks.keys())
        deleted_task_ids = set(baseline_tasks.keys()) - set(current_tasks.keys())

        new_tasks = [
            {
                "task_id": tid,
                "task_name": current_tasks[tid].get("name", "Unknown"),
                "added_after_baseline": True,
            }
            for tid in new_task_ids
        ]

        deleted_tasks = [
            {
                "task_id": tid,
                "task_name": baseline_tasks[tid].get("name", "Unknown"),
                "existed_in_baseline": True,
            }
            for tid in deleted_task_ids
        ]

        # Calculate summary statistics
        tasks_ahead = sum(1 for v in task_variances if v["is_ahead"])
        tasks_behind = sum(1 for v in task_variances if v["is_behind"])
        tasks_on_track = sum(1 for v in task_variances if v["variance_days"] == 0)

        avg_variance = (
            sum(v["variance_days"] for v in task_variances) / len(task_variances)
            if task_variances
            else 0.0
        )

        summary = {
            "total_tasks": len(current_tasks),
            "tasks_ahead": tasks_ahead,
            "tasks_behind": tasks_behind,
            "tasks_on_track": tasks_on_track,
            "avg_variance_days": round(avg_variance, 2),
            "critical_path_variance_days": 0.0,  # TODO: Calculate from critical path
        }

        return {
            "summary": summary,
            "task_variances": task_variances,
            "new_tasks": new_tasks,
            "deleted_tasks": deleted_tasks,
        }

    def _calculate_task_variance(
        self, baseline_task: Dict[str, Any], current_task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate variance for a single task.

        Args:
            baseline_task: Task data from baseline
            current_task: Current task data

        Returns:
            Dictionary with task variance details
        """
        # For MVP with minimal task data, use placeholder calculations
        # In production, this would parse dates and calculate actual variances

        # Placeholder variance calculation
        variance_days = 0  # TODO: Calculate from actual dates

        return {
            "task_id": current_task.get("id", "unknown"),
            "task_name": current_task.get("name", "Unknown Task"),
            "variance_days": variance_days,
            "is_ahead": variance_days < 0,
            "is_behind": variance_days > 0,
            "start_date_variance": 0,  # TODO: Calculate from dates
            "end_date_variance": 0,  # TODO: Calculate from dates
            "duration_variance": 0,  # TODO: Calculate from durations
            "status_changed": baseline_task.get("status") != current_task.get("status"),
            "dependencies_changed": baseline_task.get("dependencies", [])
            != current_task.get("dependencies", []),
        }
