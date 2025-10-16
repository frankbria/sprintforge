"""Monte Carlo simulation API endpoints."""

from typing import Any, Dict
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_auth
from app.database.connection import get_db
from app.schemas.simulation import (
    SimulationDetailResponse,
    SimulationHistoryItem,
    SimulationHistoryResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.services.simulation_persistence_service import SimulationPersistenceService
from app.services.simulation_service import SimulationService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["simulation"])


@router.post(
    "/{project_id}/simulate",
    response_model=SimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Monte Carlo simulation",
    description="""
    Execute probabilistic schedule simulation for a project using Monte Carlo methods.

    **Features:**
    - Support for triangular, uniform, and normal probability distributions
    - Task dependency management
    - Holiday exclusions
    - Customizable confidence intervals
    - 100-100,000 iterations for accuracy control

    **Distribution Types:**
    - **Triangular**: Requires optimistic, most_likely, and pessimistic durations
    - **Uniform**: Requires min_duration and max_duration
    - **Normal**: Requires mean and std_dev

    **Returns:**
    - Project duration estimates
    - Confidence intervals at specified percentiles
    - Statistical measures (mean, median, standard deviation)

    **Authentication:**
    Requires valid JWT token. User must own the project.
    """,
    responses={
        200: {
            "description": "Simulation completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "project_id": "123e4567-e89b-12d3-a456-426614174000",
                        "project_duration_days": 8.5,
                        "confidence_intervals": {
                            "10": 6.0,
                            "50": 8.5,
                            "90": 11.0,
                            "95": 12.0,
                            "99": 14.0,
                        },
                        "mean_duration": 8.5,
                        "median_duration": 8.5,
                        "std_deviation": 2.1,
                        "iterations_run": 10000,
                        "simulation_timestamp": "2025-01-15T10:30:00Z",
                        "task_count": 2,
                    }
                }
            },
        },
        400: {"description": "Bad request - Invalid simulation parameters"},
        401: {"description": "Unauthorized - Missing or invalid authentication token"},
        404: {"description": "Not found - Project does not exist"},
        422: {"description": "Validation error - Invalid request format"},
        500: {"description": "Internal server error - Simulation execution failed"},
    },
)
async def run_project_simulation(
    project_id: UUID,
    request: SimulationRequest,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> SimulationResponse:
    """
    Run Monte Carlo simulation for a project.

    This endpoint executes a probabilistic schedule simulation using Monte Carlo methods
    to estimate project completion times with confidence intervals.

    Args:
        project_id: Project UUID
        request: Simulation parameters including tasks, distributions, and iterations
        user_info: Authenticated user information from JWT token
        db: Database session

    Returns:
        SimulationResponse with duration estimates and confidence intervals

    Raises:
        HTTPException:
            - 400: Invalid simulation parameters
            - 401: Authentication failed
            - 404: Project not found
            - 422: Request validation failed
            - 500: Simulation execution error
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Starting Monte Carlo simulation",
        project_id=str(project_id),
        user_id=str(user_id),
        task_count=len(request.tasks),
        iterations=request.iterations,
    )

    try:
        # Initialize simulation service
        simulation_service = SimulationService(db)

        # Execute simulation
        result = await simulation_service.run_simulation(
            project_id=project_id,
            user_id=user_id,
            tasks=request.tasks,
            project_start_date=request.project_start_date,
            iterations=request.iterations,
            holidays=request.holidays,
            percentiles=request.percentiles,
        )

        logger.info(
            "Simulation completed successfully",
            project_id=str(project_id),
            user_id=str(user_id),
            duration=result.get("project_duration_days"),
            iterations=result.get("iterations_run"),
        )

        return SimulationResponse(**result)

    except ValueError as e:
        # Handle validation errors and not found errors
        error_msg = str(e).lower()

        if "not found" in error_msg:
            logger.warning(
                "Project not found",
                project_id=str(project_id),
                user_id=str(user_id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {str(e)}",
            )
        else:
            logger.warning(
                "Invalid simulation parameters",
                project_id=str(project_id),
                user_id=str(user_id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid simulation parameters: {str(e)}",
            )

    except PermissionError as e:
        # Handle authorization errors
        logger.warning(
            "Unauthorized simulation attempt",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",  # Don't reveal existence to unauthorized users
        )

    except RuntimeError as e:
        # Handle simulation execution errors
        logger.error(
            "Simulation execution failed",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulation execution failed. Please try again or reduce iteration count.",
        )

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(
            "Unexpected error during simulation",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please contact support if this persists.",
        )


@router.get(
    "/{project_id}/simulations",
    response_model=SimulationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project simulation history",
    description="""
    Retrieve historical Monte Carlo simulation results for a project.

    Returns simulation history ordered by most recent first with pagination support.

    **Query Parameters:**
    - **page**: Page number (0-indexed, default: 0)
    - **page_size**: Results per page (1-100, default: 10)

    **Authentication:**
    Requires valid JWT token. User must own the project.
    """,
)
async def get_project_simulations(
    project_id: UUID,
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Results per page"),
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> SimulationHistoryResponse:
    """
    Get simulation history for a project.

    Args:
        project_id: Project UUID
        page: Page number (0-indexed)
        page_size: Number of results per page (1-100)
        user_info: Authenticated user information
        db: Database session

    Returns:
        SimulationHistoryResponse with paginated simulation results

    Raises:
        HTTPException:
            - 401: Authentication failed
            - 404: Project not found or access denied
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Fetching simulation history",
        project_id=str(project_id),
        user_id=str(user_id),
        page=page,
        page_size=page_size,
    )

    try:
        # Initialize services
        persistence_service = SimulationPersistenceService()

        # Calculate offset from page number
        offset = page * page_size

        # Fetch simulations
        simulations = await persistence_service.get_project_simulation_history(
            db=db, project_id=project_id, limit=page_size, offset=offset
        )

        # Get total count for pagination
        total_count = await persistence_service.count_project_simulations(
            db=db, project_id=project_id
        )

        # Convert to response models
        simulation_items = [
            SimulationHistoryItem.model_validate(sim) for sim in simulations
        ]

        return SimulationHistoryResponse(
            simulations=simulation_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(
            "Failed to fetch simulation history",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve simulation history",
        )


@router.get(
    "/simulations/{simulation_id}",
    response_model=SimulationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get simulation result details",
    description="""
    Retrieve detailed information for a specific simulation result.

    **Authentication:**
    Requires valid JWT token. User must have access to the associated project.
    """,
)
async def get_simulation_detail(
    simulation_id: int,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> SimulationDetailResponse:
    """
    Get detailed simulation result by ID.

    Args:
        simulation_id: Simulation result ID
        user_info: Authenticated user information
        db: Database session

    Returns:
        SimulationDetailResponse with complete simulation details

    Raises:
        HTTPException:
            - 401: Authentication failed
            - 404: Simulation not found or access denied
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Fetching simulation detail",
        simulation_id=simulation_id,
        user_id=str(user_id),
    )

    try:
        # Initialize service
        persistence_service = SimulationPersistenceService()

        # Fetch simulation
        simulation = await persistence_service.get_simulation_result(db, simulation_id)

        if simulation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation not found",
            )

        # Convert to response model
        return SimulationDetailResponse.model_validate(simulation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch simulation detail",
            simulation_id=simulation_id,
            user_id=str(user_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve simulation details",
        )
