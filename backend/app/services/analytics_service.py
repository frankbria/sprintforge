"""
Analytics service for project health metrics and insights.

Provides comprehensive analytics including health scores, critical path analysis,
resource utilization, simulation summaries, and progress tracking.
"""

import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.project import Project
from app.models.simulation_result import SimulationResult
from app.services.scheduler.cpm import calculate_critical_path
from app.services.scheduler.task_graph import TaskGraph

logger = logging.getLogger(__name__)


class AnalyticsError(Exception):
    """Raised when analytics calculation fails."""

    pass


class AnalyticsService:
    """
    Service for calculating project analytics and metrics.

    Provides analytics functions with Redis caching for performance.
    Cache TTL is 5 minutes (300 seconds) by default.
    """

    def __init__(self, cache_ttl: int = 300):
        """
        Initialize analytics service.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.cache_ttl = cache_ttl
        self._redis_client: Optional[redis.Redis] = None

    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get Redis client, initializing if needed."""
        if self._redis_client is None:
            try:
                self._redis_client = await redis.from_url(
                    settings.redis_url, encoding="utf-8", decode_responses=True
                )
                # Test connection
                await self._redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self._redis_client = None
        return self._redis_client

    async def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value by key."""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                cached = await redis_client.get(key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed for {key}: {e}")
        return None

    async def _set_cached(self, key: str, value: Dict[str, Any]) -> None:
        """Set cached value with TTL."""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                await redis_client.setex(
                    key, self.cache_ttl, json.dumps(value, default=str)
                )
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")

    async def calculate_project_health_score(
        self, project_id: UUID, db: AsyncSession
    ) -> float:
        """
        Calculate overall project health score (0-100).

        Factors:
        - Schedule adherence (30%): Are we on track vs baseline?
        - Critical path stability (25%): How stable is the critical path?
        - Resource utilization (20%): Are resources properly allocated?
        - Risk level (15%): Monte Carlo P90 vs P50 spread
        - Completion rate (10%): Task completion velocity

        Args:
            project_id: UUID of the project
            db: Database session

        Returns:
            float: Health score 0-100 (100 = excellent health)

        Raises:
            AnalyticsError: If calculation fails
        """
        cache_key = f"analytics:health:{project_id}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached["health_score"]

        try:
            # Get project
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                raise AnalyticsError(f"Project {project_id} not found")

            # Get latest simulation result for risk assessment
            sim_result = await db.execute(
                select(SimulationResult)
                .where(SimulationResult.project_id == project_id)
                .order_by(SimulationResult.created_at.desc())
                .limit(1)
            )
            latest_sim = sim_result.scalar_one_or_none()

            # Calculate component scores
            schedule_score = await self._calculate_schedule_adherence_score(
                project, db
            )
            critical_path_score = await self._calculate_critical_path_stability_score(
                project, db
            )
            resource_score = await self._calculate_resource_utilization_score(
                project, db
            )
            risk_score = self._calculate_risk_score(latest_sim) if latest_sim else 50.0
            completion_score = await self._calculate_completion_rate_score(project, db)

            # Weighted average
            health_score = (
                schedule_score * 0.30
                + critical_path_score * 0.25
                + resource_score * 0.20
                + risk_score * 0.15
                + completion_score * 0.10
            )

            # Cache result
            await self._set_cached(cache_key, {"health_score": health_score})

            return round(health_score, 2)

        except Exception as e:
            logger.error(f"Health score calculation failed: {e}")
            raise AnalyticsError(f"Failed to calculate health score: {e}") from e

    async def get_critical_path_metrics(
        self, project_id: UUID, db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get critical path analysis metrics.

        Args:
            project_id: UUID of the project
            db: Database session

        Returns:
            {
                "critical_tasks": List[task_ids],
                "total_duration": int,  # days
                "float_time": Dict[task_id, float_days],
                "risk_tasks": List[task_ids],  # high risk items
                "path_stability_score": float  # 0-100
            }

        Raises:
            AnalyticsError: If calculation fails
        """
        cache_key = f"analytics:critical_path:{project_id}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # Get project configuration
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                raise AnalyticsError(f"Project {project_id} not found")

            # Extract task data from configuration
            tasks_data = project.configuration.get("tasks", [])
            if not tasks_data:
                # Return empty metrics for projects without tasks
                metrics = {
                    "critical_tasks": [],
                    "total_duration": 0,
                    "float_time": {},
                    "risk_tasks": [],
                    "path_stability_score": 100.0,
                }
                await self._set_cached(cache_key, metrics)
                return metrics

            # Build task graph
            graph = TaskGraph()
            durations = {}

            for task in tasks_data:
                task_id = task.get("id", task.get("task_id"))
                duration = float(task.get("duration", 1.0))
                dependencies = task.get("dependencies", [])

                graph.add_node(task_id)
                durations[task_id] = duration

                for dep in dependencies:
                    graph.add_edge(dep, task_id)

            # Calculate critical path
            cpm_result = calculate_critical_path(graph, durations)

            # Calculate float time for each task
            float_time = {}
            for task_id, task_data in cpm_result.tasks.items():
                float_time[task_id] = round(task_data.slack, 2)

            # Identify high-risk tasks (low slack, high duration)
            risk_tasks = []
            for task_id, task_data in cpm_result.tasks.items():
                # Tasks with slack < 2 days and duration > 5 days are risky
                if task_data.slack < 2.0 and task_data.duration > 5.0:
                    risk_tasks.append(task_id)

            # Calculate path stability score
            path_stability_score = await self._calculate_critical_path_stability_score(
                project, db
            )

            metrics = {
                "critical_tasks": cpm_result.critical_path,
                "total_duration": round(cpm_result.project_duration, 2),
                "float_time": float_time,
                "risk_tasks": risk_tasks,
                "path_stability_score": round(path_stability_score, 2),
            }

            await self._set_cached(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Critical path metrics calculation failed: {e}")
            raise AnalyticsError(
                f"Failed to calculate critical path metrics: {e}"
            ) from e

    async def get_resource_utilization(
        self, project_id: UUID, db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Calculate resource allocation and utilization metrics.

        Args:
            project_id: UUID of the project
            db: Database session

        Returns:
            {
                "total_resources": int,
                "allocated_resources": int,
                "utilization_pct": float,
                "over_allocated": List[resource_info],
                "under_utilized": List[resource_info],
                "resource_timeline": Dict[date, utilization_pct]
            }

        Raises:
            AnalyticsError: If calculation fails
        """
        cache_key = f"analytics:resources:{project_id}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # Get project
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                raise AnalyticsError(f"Project {project_id} not found")

            # Extract resource data from configuration
            tasks_data = project.configuration.get("tasks", [])
            resources_data = project.configuration.get("resources", {})

            # Track resource allocation by task
            resource_allocation: Dict[str, List[str]] = defaultdict(list)
            resource_workload: Dict[str, float] = defaultdict(float)

            for task in tasks_data:
                task_id = task.get("id", task.get("task_id"))
                assigned_resources = task.get("resources", [])
                duration = float(task.get("duration", 1.0))

                for resource in assigned_resources:
                    resource_allocation[resource].append(task_id)
                    resource_workload[resource] += duration

            # Calculate metrics
            total_resources = len(resources_data) if resources_data else len(
                resource_allocation
            )
            allocated_resources = len(resource_allocation)

            # Over-allocated: resources with > 40 days of work
            over_allocated = []
            for resource, workload in resource_workload.items():
                if workload > 40:
                    over_allocated.append(
                        {
                            "resource_id": resource,
                            "workload_days": round(workload, 2),
                            "tasks_count": len(resource_allocation[resource]),
                        }
                    )

            # Under-utilized: resources with < 10 days of work
            under_utilized = []
            for resource, workload in resource_workload.items():
                if workload < 10:
                    under_utilized.append(
                        {
                            "resource_id": resource,
                            "workload_days": round(workload, 2),
                            "tasks_count": len(resource_allocation[resource]),
                        }
                    )

            # Calculate overall utilization percentage
            # Assuming 40 hours/week, 5 days/week, typical sprint is 2 weeks = 10 days
            target_utilization = total_resources * 20 if total_resources > 0 else 1
            actual_utilization = sum(resource_workload.values())
            utilization_pct = (
                min(actual_utilization / target_utilization * 100, 100)
                if target_utilization > 0
                else 0
            )

            # Generate resource timeline (placeholder - would need task dates)
            resource_timeline = {}

            metrics = {
                "total_resources": total_resources,
                "allocated_resources": allocated_resources,
                "utilization_pct": round(utilization_pct, 2),
                "over_allocated": over_allocated,
                "under_utilized": under_utilized,
                "resource_timeline": resource_timeline,
            }

            await self._set_cached(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Resource utilization calculation failed: {e}")
            raise AnalyticsError(
                f"Failed to calculate resource utilization: {e}"
            ) from e

    async def get_simulation_summary(
        self, project_id: UUID, db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Aggregate Monte Carlo simulation results.

        Args:
            project_id: UUID of the project
            db: Database session

        Returns:
            {
                "percentiles": {
                    "p10": float,
                    "p50": float,
                    "p75": float,
                    "p90": float,
                    "p95": float
                },
                "mean_duration": float,
                "std_deviation": float,
                "risk_level": str,  # "low", "medium", "high"
                "confidence_80pct_range": [min, max],
                "histogram_data": List[{bucket: count}]
            }

        Raises:
            AnalyticsError: If calculation fails
        """
        cache_key = f"analytics:simulation:{project_id}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # Get latest simulation result
            result = await db.execute(
                select(SimulationResult)
                .where(SimulationResult.project_id == project_id)
                .order_by(SimulationResult.created_at.desc())
                .limit(1)
            )
            sim_result = result.scalar_one_or_none()

            if not sim_result:
                # Return default values if no simulation exists
                summary = {
                    "percentiles": {
                        "p10": 0.0,
                        "p50": 0.0,
                        "p75": 0.0,
                        "p90": 0.0,
                        "p95": 0.0,
                    },
                    "mean_duration": 0.0,
                    "std_deviation": 0.0,
                    "risk_level": "unknown",
                    "confidence_80pct_range": [0.0, 0.0],
                    "histogram_data": [],
                }
                await self._set_cached(cache_key, summary)
                return summary

            # Extract percentiles from confidence_intervals
            confidence_intervals = sim_result.confidence_intervals
            percentiles = {
                "p10": confidence_intervals.get(10, 0.0),
                "p50": confidence_intervals.get(50, sim_result.median_duration),
                "p75": confidence_intervals.get(75, 0.0),
                "p90": confidence_intervals.get(90, 0.0),
                "p95": confidence_intervals.get(95, 0.0),
            }

            # Calculate risk level based on P90/P50 spread
            p50 = percentiles["p50"]
            p90 = percentiles["p90"]

            if p50 > 0:
                spread_pct = ((p90 - p50) / p50) * 100
                if spread_pct < 15:
                    risk_level = "low"
                elif spread_pct < 30:
                    risk_level = "medium"
                else:
                    risk_level = "high"
            else:
                risk_level = "unknown"

            # 80% confidence interval (P10 to P90)
            confidence_80pct_range = [percentiles["p10"], percentiles["p90"]]

            # Generate histogram data (placeholder - would need raw simulation data)
            # For now, create bins based on percentiles
            histogram_data = [
                {"bucket": "P0-P10", "range": [0, percentiles["p10"]], "probability": 10},
                {
                    "bucket": "P10-P50",
                    "range": [percentiles["p10"], percentiles["p50"]],
                    "probability": 40,
                },
                {
                    "bucket": "P50-P90",
                    "range": [percentiles["p50"], percentiles["p90"]],
                    "probability": 40,
                },
                {
                    "bucket": "P90-P100",
                    "range": [percentiles["p90"], percentiles["p90"] * 1.2],
                    "probability": 10,
                },
            ]

            summary = {
                "percentiles": percentiles,
                "mean_duration": round(sim_result.mean_duration, 2),
                "std_deviation": round(sim_result.std_deviation, 2),
                "risk_level": risk_level,
                "confidence_80pct_range": [
                    round(confidence_80pct_range[0], 2),
                    round(confidence_80pct_range[1], 2),
                ],
                "histogram_data": histogram_data,
            }

            await self._set_cached(cache_key, summary)
            return summary

        except Exception as e:
            logger.error(f"Simulation summary calculation failed: {e}")
            raise AnalyticsError(f"Failed to calculate simulation summary: {e}") from e

    async def get_progress_metrics(
        self, project_id: UUID, db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Calculate progress tracking metrics.

        Args:
            project_id: UUID of the project
            db: Database session

        Returns:
            {
                "completion_pct": float,
                "tasks_completed": int,
                "tasks_total": int,
                "on_time_pct": float,
                "delayed_tasks": int,
                "burn_rate": float,  # tasks per day
                "estimated_completion_date": date,
                "variance_from_plan": int  # days ahead/behind
            }

        Raises:
            AnalyticsError: If calculation fails
        """
        cache_key = f"analytics:progress:{project_id}"
        cached = await self._get_cached(cache_key)
        if cached:
            # Convert date string back to date object
            if "estimated_completion_date" in cached and cached["estimated_completion_date"]:
                cached["estimated_completion_date"] = datetime.fromisoformat(
                    cached["estimated_completion_date"]
                ).date()
            return cached

        try:
            # Get project
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                raise AnalyticsError(f"Project {project_id} not found")

            # Extract task data
            tasks_data = project.configuration.get("tasks", [])
            if not tasks_data:
                metrics = {
                    "completion_pct": 0.0,
                    "tasks_completed": 0,
                    "tasks_total": 0,
                    "on_time_pct": 0.0,
                    "delayed_tasks": 0,
                    "burn_rate": 0.0,
                    "estimated_completion_date": None,
                    "variance_from_plan": 0,
                }
                await self._set_cached(cache_key, metrics)
                return metrics

            # Calculate completion metrics
            tasks_total = len(tasks_data)
            tasks_completed = sum(
                1 for task in tasks_data if task.get("status") == "completed"
            )
            completion_pct = (
                (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0
            )

            # Calculate on-time percentage
            on_time_tasks = sum(
                1
                for task in tasks_data
                if task.get("status") == "completed" and not task.get("is_delayed", False)
            )
            on_time_pct = (
                (on_time_tasks / tasks_completed * 100) if tasks_completed > 0 else 0
            )

            # Count delayed tasks
            delayed_tasks = sum(1 for task in tasks_data if task.get("is_delayed", False))

            # Calculate burn rate (tasks per day)
            # Estimate based on project age and completed tasks
            project_age_days = (datetime.now() - project.created_at).days
            if project_age_days > 0:
                burn_rate = tasks_completed / project_age_days
            else:
                burn_rate = 0.0

            # Estimate completion date
            remaining_tasks = tasks_total - tasks_completed
            if burn_rate > 0:
                days_to_completion = remaining_tasks / burn_rate
                estimated_completion_date = date.today() + timedelta(
                    days=int(days_to_completion)
                )
            else:
                estimated_completion_date = None

            # Calculate variance from plan
            # Get baseline from simulation or configuration
            result = await db.execute(
                select(SimulationResult)
                .where(SimulationResult.project_id == project_id)
                .order_by(SimulationResult.created_at.asc())
                .limit(1)
            )
            baseline_sim = result.scalar_one_or_none()

            if baseline_sim and estimated_completion_date:
                # Compare to baseline median duration
                baseline_days = baseline_sim.median_duration
                actual_days = (estimated_completion_date - baseline_sim.project_start_date).days
                variance_from_plan = actual_days - int(baseline_days)
            else:
                variance_from_plan = 0

            metrics = {
                "completion_pct": round(completion_pct, 2),
                "tasks_completed": tasks_completed,
                "tasks_total": tasks_total,
                "on_time_pct": round(on_time_pct, 2),
                "delayed_tasks": delayed_tasks,
                "burn_rate": round(burn_rate, 3),
                "estimated_completion_date": estimated_completion_date,
                "variance_from_plan": variance_from_plan,
            }

            await self._set_cached(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Progress metrics calculation failed: {e}")
            raise AnalyticsError(f"Failed to calculate progress metrics: {e}") from e

    # Helper methods for health score calculation

    async def _calculate_schedule_adherence_score(
        self, project: Project, db: AsyncSession
    ) -> float:
        """Calculate schedule adherence component (0-100)."""
        # Placeholder: would compare actual vs planned dates
        # For now, return 80 as a reasonable baseline
        return 80.0

    async def _calculate_critical_path_stability_score(
        self, project: Project, db: AsyncSession
    ) -> float:
        """Calculate critical path stability component (0-100)."""
        # Stable critical path = high score
        # For now, return 85 as baseline
        return 85.0

    async def _calculate_resource_utilization_score(
        self, project: Project, db: AsyncSession
    ) -> float:
        """Calculate resource utilization component (0-100)."""
        # Target 70-90% utilization as optimal
        metrics = await self.get_resource_utilization(project.id, db)
        utilization = metrics["utilization_pct"]

        if 70 <= utilization <= 90:
            return 100.0
        elif utilization < 70:
            # Under-utilized: score decreases as utilization drops
            return max(50, utilization / 70 * 100)
        else:
            # Over-utilized: score decreases as utilization increases
            return max(50, 200 - utilization)

    def _calculate_risk_score(self, sim_result: SimulationResult) -> float:
        """Calculate risk component based on simulation (0-100)."""
        # Lower risk = higher score
        confidence_intervals = sim_result.confidence_intervals
        p50 = confidence_intervals.get(50, sim_result.median_duration)
        p90 = confidence_intervals.get(90, p50 * 1.5)

        if p50 > 0:
            spread_pct = ((p90 - p50) / p50) * 100
            # Low spread (<15%) = high score (90-100)
            # Medium spread (15-30%) = medium score (60-90)
            # High spread (>30%) = low score (30-60)
            if spread_pct < 15:
                return 95.0
            elif spread_pct < 30:
                return 75.0
            else:
                return 50.0
        return 50.0

    async def _calculate_completion_rate_score(
        self, project: Project, db: AsyncSession
    ) -> float:
        """Calculate completion rate component (0-100)."""
        metrics = await self.get_progress_metrics(project.id, db)
        completion_pct = metrics["completion_pct"]

        # Higher completion = higher score
        # Also factor in on-time percentage
        on_time_pct = metrics["on_time_pct"]

        # Weighted: 70% completion, 30% on-time
        return completion_pct * 0.7 + on_time_pct * 0.3

    async def close(self) -> None:
        """Close Redis connection if open."""
        if self._redis_client:
            await self._redis_client.close()
