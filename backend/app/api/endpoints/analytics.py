"""Analytics API endpoints for project insights and metrics."""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.auth import require_auth
from app.database.connection import get_db
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    CriticalPathResponse,
    ResourceUtilizationResponse,
    SimulationSummaryResponse,
    ProgressMetricsResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.project_service import ProjectService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["analytics"])


async def get_analytics_service() -> AnalyticsService:
    """Dependency for getting analytics service instance."""
    return AnalyticsService()


async def verify_project_access(
    project_id: UUID,
    user_info: Dict[str, Any],
    db: AsyncSession,
) -> None:
    """Verify user has access to the project.

    Args:
        project_id: Project UUID
        user_info: Authenticated user information
        db: Database session

    Raises:
        HTTPException: If project not found or access denied
    """
    user_id = UUID(user_info.get("sub"))
    project_service = ProjectService(db)

    # Check ownership
    if not await project_service.check_owner_permission(project_id, user_id):
        logger.warning(
            "Unauthorized analytics access attempt",
            project_id=str(project_id),
            user_id=str(user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Verify project exists
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


@router.get(
    "/{project_id}/analytics/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Get analytics overview",
    description="Get comprehensive analytics overview with all key metrics in a single response.",
    responses={
        200: {"description": "Analytics overview retrieved successfully"},
        404: {"description": "Project not found"},
        403: {"description": "Access denied"},
        500: {"description": "Internal server error"},
    },
)
async def get_analytics_overview(
    project_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsOverviewResponse:
    """Get comprehensive analytics overview.

    Returns all key metrics in a single response:
    - Health score
    - Critical path summary
    - Resource utilization summary
    - Latest simulation results
    - Progress metrics

    Args:
        project_id: Project UUID
        user_info: Authenticated user information from JWT
        db: Database session
        analytics_service: Analytics service instance

    Returns:
        Analytics overview with all key metrics

    Raises:
        HTTPException: If project not found or access denied
    """
    logger.info(
        "Getting analytics overview",
        project_id=str(project_id),
        user_id=user_info.get("sub"),
    )

    try:
        # Verify project access
        await verify_project_access(project_id, user_info, db)

        # Calculate all metrics
        health_score = await analytics_service.calculate_project_health_score(project_id, db)
        critical_path = await analytics_service.get_critical_path_metrics(project_id, db)
        resources = await analytics_service.get_resource_utilization(project_id, db)
        simulation = await analytics_service.get_simulation_summary(project_id, db)
        progress = await analytics_service.get_progress_metrics(project_id, db)

        # Build summary dictionaries
        critical_path_summary = {
            "total_duration": critical_path["total_duration"],
            "critical_tasks_count": len(critical_path["critical_tasks"]),
            "stability_score": critical_path["path_stability_score"],
        }

        resource_summary = {
            "utilization_pct": resources["utilization_pct"],
            "over_allocated_count": len(resources["over_allocated"]),
            "under_utilized_count": len(resources["under_utilized"]),
        }

        simulation_summary = {
            "risk_level": simulation["risk_level"],
            "p50_duration": simulation["percentiles"]["p50"],
            "p90_duration": simulation["percentiles"]["p90"],
        }

        progress_summary = {
            "completion_pct": progress["completion_pct"],
            "on_time_pct": progress["on_time_pct"],
            "variance_from_plan": progress["variance_from_plan"],
        }

        logger.info(
            "Analytics overview retrieved successfully",
            project_id=str(project_id),
            health_score=health_score,
        )

        return AnalyticsOverviewResponse(
            health_score=health_score,
            critical_path_summary=critical_path_summary,
            resource_summary=resource_summary,
            simulation_summary=simulation_summary,
            progress_summary=progress_summary,
            generated_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting analytics overview",
            project_id=str(project_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics overview",
        )


@router.get(
    "/{project_id}/analytics/critical-path",
    response_model=CriticalPathResponse,
    summary="Get critical path analysis",
    description="Get detailed critical path analysis including critical tasks, duration, and stability metrics.",
)
async def get_critical_path_analytics(
    project_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> CriticalPathResponse:
    """Get detailed critical path analysis.

    Args:
        project_id: Project UUID
        user_info: Authenticated user information from JWT
        db: Database session
        analytics_service: Analytics service instance

    Returns:
        Critical path metrics and analysis

    Raises:
        HTTPException: If project not found or access denied
    """
    logger.info(
        "Getting critical path analytics",
        project_id=str(project_id),
        user_id=user_info.get("sub"),
    )

    try:
        # Verify project access
        await verify_project_access(project_id, user_info, db)

        # Get critical path metrics
        metrics = await analytics_service.get_critical_path_metrics(project_id, db)

        logger.info(
            "Critical path analytics retrieved successfully",
            project_id=str(project_id),
            critical_tasks_count=len(metrics["critical_tasks"]),
        )

        return CriticalPathResponse(**metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting critical path analytics",
            project_id=str(project_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve critical path analytics",
        )


@router.get(
    "/{project_id}/analytics/resources",
    response_model=ResourceUtilizationResponse,
    summary="Get resource utilization metrics",
    description="Get resource allocation and utilization metrics including over-allocated and under-utilized resources.",
)
async def get_resource_analytics(
    project_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ResourceUtilizationResponse:
    """Get resource utilization metrics.

    Args:
        project_id: Project UUID
        user_info: Authenticated user information from JWT
        db: Database session
        analytics_service: Analytics service instance

    Returns:
        Resource utilization metrics

    Raises:
        HTTPException: If project not found or access denied
    """
    logger.info(
        "Getting resource analytics",
        project_id=str(project_id),
        user_id=user_info.get("sub"),
    )

    try:
        # Verify project access
        await verify_project_access(project_id, user_info, db)

        # Get resource metrics
        metrics = await analytics_service.get_resource_utilization(project_id, db)

        logger.info(
            "Resource analytics retrieved successfully",
            project_id=str(project_id),
            utilization_pct=metrics["utilization_pct"],
        )

        return ResourceUtilizationResponse(**metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting resource analytics",
            project_id=str(project_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resource analytics",
        )


@router.get(
    "/{project_id}/analytics/simulation",
    response_model=SimulationSummaryResponse,
    summary="Get Monte Carlo simulation summary",
    description="Get aggregated Monte Carlo simulation results including percentiles, risk level, and distribution.",
)
async def get_simulation_analytics(
    project_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> SimulationSummaryResponse:
    """Get Monte Carlo simulation summary.

    Args:
        project_id: Project UUID
        user_info: Authenticated user information from JWT
        db: Database session
        analytics_service: Analytics service instance

    Returns:
        Simulation summary with percentiles and risk metrics

    Raises:
        HTTPException: If project not found or access denied
    """
    logger.info(
        "Getting simulation analytics",
        project_id=str(project_id),
        user_id=user_info.get("sub"),
    )

    try:
        # Verify project access
        await verify_project_access(project_id, user_info, db)

        # Get simulation summary
        summary = await analytics_service.get_simulation_summary(project_id, db)

        logger.info(
            "Simulation analytics retrieved successfully",
            project_id=str(project_id),
            risk_level=summary["risk_level"],
        )

        return SimulationSummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting simulation analytics",
            project_id=str(project_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve simulation analytics",
        )


@router.get(
    "/{project_id}/analytics/progress",
    response_model=ProgressMetricsResponse,
    summary="Get progress tracking metrics",
    description="Get progress tracking metrics including completion percentage, burn rate, and schedule variance.",
)
async def get_progress_analytics(
    project_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ProgressMetricsResponse:
    """Get progress tracking metrics.

    Args:
        project_id: Project UUID
        user_info: Authenticated user information from JWT
        db: Database session
        analytics_service: Analytics service instance

    Returns:
        Progress tracking metrics

    Raises:
        HTTPException: If project not found or access denied
    """
    logger.info(
        "Getting progress analytics",
        project_id=str(project_id),
        user_id=user_info.get("sub"),
    )

    try:
        # Verify project access
        await verify_project_access(project_id, user_info, db)

        # Get progress metrics
        metrics = await analytics_service.get_progress_metrics(project_id, db)

        logger.info(
            "Progress analytics retrieved successfully",
            project_id=str(project_id),
            completion_pct=metrics["completion_pct"],
        )

        return ProgressMetricsResponse(**metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting progress analytics",
            project_id=str(project_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve progress analytics",
        )
