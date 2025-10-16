"""
Simulation persistence service for database operations.

Handles CRUD operations for Monte Carlo simulation results.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulation_result import SimulationResult
from app.services.scheduler.monte_carlo import MonteCarloResult

logger = structlog.get_logger(__name__)


class SimulationPersistenceService:
    """
    Service for persisting and querying Monte Carlo simulation results.

    Provides CRUD operations for simulation results with support for
    pagination and filtering.
    """

    async def save_simulation_result(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        simulation_result: MonteCarloResult,
        project_start_date: date,
        task_count: int,
        execution_time: Optional[float] = None,
    ) -> SimulationResult:
        """
        Save Monte Carlo simulation result to database.

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User UUID
            simulation_result: MonteCarloResult from simulation engine
            project_start_date: Project start date used in simulation
            task_count: Number of tasks in simulation
            execution_time: Optional simulation execution time in seconds

        Returns:
            SimulationResult: Saved database record

        Raises:
            ValueError: If simulation result is invalid
        """
        # Validate inputs
        if simulation_result.iterations <= 0:
            raise ValueError("Iterations must be positive")
        if task_count <= 0:
            raise ValueError("Task count must be positive")

        # Create database record
        db_simulation = SimulationResult(
            project_id=project_id,
            user_id=user_id,
            iterations=simulation_result.iterations,
            task_count=task_count,
            project_start_date=project_start_date,
            mean_duration=simulation_result.mean_duration,
            median_duration=simulation_result.median_duration,
            std_deviation=simulation_result.std_dev,
            confidence_intervals=simulation_result.percentiles,
            simulation_duration_seconds=execution_time,
        )

        db.add(db_simulation)
        await db.commit()
        await db.refresh(db_simulation)

        logger.info(
            "simulation_saved",
            simulation_id=db_simulation.id,
            project_id=str(project_id),
            iterations=simulation_result.iterations,
        )

        return db_simulation

    async def get_simulation_result(
        self, db: AsyncSession, simulation_id: int
    ) -> Optional[SimulationResult]:
        """
        Retrieve simulation result by ID.

        Args:
            db: Database session
            simulation_id: Simulation result ID

        Returns:
            SimulationResult or None if not found
        """
        result = await db.execute(
            select(SimulationResult).where(SimulationResult.id == simulation_id)
        )
        return result.scalar_one_or_none()

    async def get_project_simulation_history(
        self,
        db: AsyncSession,
        project_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> List[SimulationResult]:
        """
        Get simulation history for a project.

        Returns most recent simulations first.

        Args:
            db: Database session
            project_id: Project UUID
            limit: Maximum number of results (default 10, max 100)
            offset: Number of results to skip (default 0)

        Returns:
            List of SimulationResult ordered by created_at DESC
        """
        # Enforce limits
        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        result = await db.execute(
            select(SimulationResult)
            .where(SimulationResult.project_id == project_id)
            .order_by(desc(SimulationResult.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_user_simulation_history(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> List[SimulationResult]:
        """
        Get simulation history for a user.

        Returns most recent simulations first.

        Args:
            db: Database session
            user_id: User UUID
            limit: Maximum number of results (default 10, max 100)
            offset: Number of results to skip (default 0)

        Returns:
            List of SimulationResult ordered by created_at DESC
        """
        # Enforce limits
        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        result = await db.execute(
            select(SimulationResult)
            .where(SimulationResult.user_id == user_id)
            .order_by(desc(SimulationResult.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete_simulation_result(
        self, db: AsyncSession, simulation_id: int
    ) -> bool:
        """
        Delete simulation result by ID.

        Args:
            db: Database session
            simulation_id: Simulation result ID

        Returns:
            True if deleted, False if not found
        """
        simulation = await self.get_simulation_result(db, simulation_id)

        if simulation is None:
            return False

        await db.delete(simulation)
        await db.commit()

        logger.info("simulation_deleted", simulation_id=simulation_id)

        return True

    async def count_project_simulations(
        self, db: AsyncSession, project_id: UUID
    ) -> int:
        """
        Count total simulations for a project.

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            Total count of simulations
        """
        from sqlalchemy import func as sql_func

        result = await db.execute(
            select(sql_func.count(SimulationResult.id)).where(
                SimulationResult.project_id == project_id
            )
        )
        return result.scalar_one()
