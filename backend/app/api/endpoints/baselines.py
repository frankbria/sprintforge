"""Project baseline management API endpoints."""

from typing import Any, Dict
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_auth
from app.database.connection import get_db
from app.models.baseline import ProjectBaseline
from app.schemas.baseline import (
    BaselineComparisonResponse,
    BaselineDetailResponse,
    BaselineListResponse,
    BaselineResponse,
    CreateBaselineRequest,
    SetBaselineActiveResponse,
)
from app.services.baseline_service import BaselineService, BaselineError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["baselines"])


@router.post(
    "/{project_id}/baselines",
    response_model=BaselineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project baseline",
    description="""
    Create an immutable snapshot of the current project state.

    Baselines capture all project data at a specific point in time for future comparison.
    Used to track project progress against original plans or milestones.

    **Features:**
    - Immutable snapshot of complete project state
    - SERIALIZABLE transaction isolation for consistency
    - Automatic size validation (10MB limit)
    - Includes tasks, dependencies, critical path, Monte Carlo results

    **Authentication:**
    Requires valid JWT token. User must own the project.
    """,
)
async def create_baseline(
    project_id: UUID,
    request: CreateBaselineRequest,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> BaselineResponse:
    """Create a new baseline for a project."""
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Creating baseline",
        project_id=str(project_id),
        user_id=str(user_id),
        baseline_name=request.name,
    )

    try:
        service = BaselineService()
        baseline = await service.create_baseline(
            project_id=project_id,
            name=request.name,
            description=request.description,
            db=db,
        )

        logger.info(
            "Baseline created successfully",
            project_id=str(project_id),
            baseline_id=str(baseline.id),
            snapshot_size=baseline.snapshot_size_bytes,
        )

        return BaselineResponse.model_validate(baseline)

    except BaselineError as e:
        logger.warning(
            "Failed to create baseline",
            project_id=str(project_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        logger.warning(
            "Snapshot size limit exceeded",
            project_id=str(project_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Unexpected error creating baseline",
            project_id=str(project_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create baseline",
        )


@router.get(
    "/{project_id}/baselines",
    response_model=BaselineListResponse,
    status_code=status.HTTP_200_OK,
    summary="List project baselines",
    description="""
    Retrieve all baselines for a project with pagination.

    Returns baseline summary info without snapshot data (for performance).
    Use GET /baselines/{baseline_id} to retrieve full details.
    """,
)
async def list_baselines(
    project_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> BaselineListResponse:
    """List all baselines for a project."""
    logger.info(
        "Listing baselines",
        project_id=str(project_id),
        page=page,
        limit=limit,
    )

    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Fetch baselines
        result = await db.execute(
            select(ProjectBaseline)
            .where(ProjectBaseline.project_id == project_id)
            .order_by(desc(ProjectBaseline.created_at))
            .limit(limit)
            .offset(offset)
        )
        baselines = result.scalars().all()

        # Get total count
        count_result = await db.execute(
            select(ProjectBaseline)
            .where(ProjectBaseline.project_id == project_id)
        )
        total = len(count_result.scalars().all())

        baseline_responses = [
            BaselineResponse.model_validate(b) for b in baselines
        ]

        return BaselineListResponse(
            baselines=baseline_responses,
            total=total,
            page=page,
            limit=limit,
        )

    except Exception as e:
        logger.error(
            "Failed to list baselines",
            project_id=str(project_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve baselines",
        )


@router.get(
    "/{project_id}/baselines/{baseline_id}",
    response_model=BaselineDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get baseline details",
    description="""
    Retrieve full baseline details including snapshot data.

    Warning: Response may be large for projects with many tasks.
    """,
)
async def get_baseline(
    project_id: UUID,
    baseline_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> BaselineDetailResponse:
    """Get detailed information for a specific baseline."""
    logger.info(
        "Fetching baseline detail",
        project_id=str(project_id),
        baseline_id=str(baseline_id),
    )

    try:
        result = await db.execute(
            select(ProjectBaseline)
            .where(
                ProjectBaseline.id == baseline_id,
                ProjectBaseline.project_id == project_id,
            )
        )
        baseline = result.scalar_one_or_none()

        if not baseline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Baseline not found",
            )

        return BaselineDetailResponse.model_validate(baseline)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch baseline",
            baseline_id=str(baseline_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve baseline",
        )


@router.delete(
    "/{project_id}/baselines/{baseline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete baseline",
    description="""
    Permanently delete a baseline.

    This operation is irreversible. Baseline data cannot be recovered.
    """,
)
async def delete_baseline(
    project_id: UUID,
    baseline_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Delete a baseline."""
    logger.info(
        "Deleting baseline",
        project_id=str(project_id),
        baseline_id=str(baseline_id),
    )

    try:
        result = await db.execute(
            select(ProjectBaseline)
            .where(
                ProjectBaseline.id == baseline_id,
                ProjectBaseline.project_id == project_id,
            )
        )
        baseline = result.scalar_one_or_none()

        if not baseline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Baseline not found",
            )

        await db.delete(baseline)
        await db.commit()

        logger.info(
            "Baseline deleted successfully",
            baseline_id=str(baseline_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete baseline",
            baseline_id=str(baseline_id),
            error=str(e),
            exc_info=True,
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete baseline",
        )


@router.patch(
    "/{project_id}/baselines/{baseline_id}/activate",
    response_model=SetBaselineActiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Set baseline as active",
    description="""
    Mark a baseline as active for comparison.

    Only one baseline per project can be active. Setting a baseline as active
    will automatically deactivate any other active baselines for the project.
    """,
)
async def activate_baseline(
    project_id: UUID,
    baseline_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> SetBaselineActiveResponse:
    """Set a baseline as the active baseline for comparison."""
    logger.info(
        "Activating baseline",
        project_id=str(project_id),
        baseline_id=str(baseline_id),
    )

    try:
        service = BaselineService()
        baseline = await service.set_baseline_active(
            baseline_id=baseline_id,
            project_id=project_id,
            db=db,
        )

        logger.info(
            "Baseline activated successfully",
            baseline_id=str(baseline_id),
        )

        return SetBaselineActiveResponse(
            id=baseline.id,
            is_active=baseline.is_active,
            message="Baseline activated successfully",
        )

    except BaselineError as e:
        logger.warning(
            "Failed to activate baseline",
            baseline_id=str(baseline_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Unexpected error activating baseline",
            baseline_id=str(baseline_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate baseline",
        )


@router.get(
    "/{project_id}/baselines/{baseline_id}/compare",
    response_model=BaselineComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare baseline to current state",
    description="""
    Compare current project state against a baseline.

    Calculates task-level variances, identifies new/deleted tasks,
    and provides summary statistics.

    **Query Parameters:**
    - **include_unchanged**: Include tasks with zero variance (default: false)

    **Note:** Comparison results are cached for 5 minutes in Redis.
    """,
)
async def compare_baseline(
    project_id: UUID,
    baseline_id: UUID,
    include_unchanged: bool = Query(
        False, description="Include tasks with no variance"
    ),
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> BaselineComparisonResponse:
    """Compare current project state to a baseline."""
    logger.info(
        "Comparing to baseline",
        project_id=str(project_id),
        baseline_id=str(baseline_id),
        include_unchanged=include_unchanged,
    )

    try:
        service = BaselineService()
        comparison = await service.compare_to_baseline(
            baseline_id=baseline_id,
            project_id=project_id,
            db=db,
            include_unchanged=include_unchanged,
        )

        logger.info(
            "Comparison completed successfully",
            baseline_id=str(baseline_id),
            variance_count=len(comparison.get("task_variances", [])),
        )

        return BaselineComparisonResponse(**comparison)

    except BaselineError as e:
        logger.warning(
            "Failed to compare baseline",
            baseline_id=str(baseline_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Unexpected error during comparison",
            baseline_id=str(baseline_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform comparison",
        )
