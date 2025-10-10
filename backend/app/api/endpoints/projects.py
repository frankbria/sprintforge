"""Project management API endpoints."""

from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.auth import require_auth
from app.database.connection import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from app.services.project_service import ProjectService
from app.services.quota_service import QuotaService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project with Excel configuration. Requires authentication. Free tier limited to 3 active projects.",
    responses={
        201: {"description": "Project created successfully"},
        400: {"description": "Bad request - Invalid configuration"},
        403: {"description": "Forbidden - Project quota exceeded"},
        500: {"description": "Internal server error"},
    },
)
async def create_project(
    project_data: ProjectCreate,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Create a new project.

    **Quota Limits:**
    - Free tier: 3 active projects
    - Pro tier: Unlimited projects
    - Enterprise tier: Unlimited projects

    Args:
        project_data: Project creation data including configuration
        user_info: Authenticated user information from JWT
        db: Database session

    Returns:
        Created project with ID and timestamps

    Raises:
        HTTPException: If validation fails, quota exceeded, or creation error occurs
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Creating project",
        user_id=str(user_id),
        project_name=project_data.name,
    )

    try:
        # Check project quota BEFORE creating
        quota_service = QuotaService(db)
        await quota_service.check_project_quota(user_id)

        service = ProjectService(db)
        project = await service.create_project(user_id, project_data)

        logger.info(
            "Project created successfully",
            project_id=str(project.id),
            user_id=str(user_id),
        )

        return ProjectResponse.model_validate(project)

    except ValueError as e:
        logger.warning(
            "Invalid project configuration",
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}",
        )
    except Exception as e:
        logger.error(
            "Error creating project",
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List user projects",
    description="Get paginated list of projects owned by authenticated user with optional search and sorting.",
)
async def list_projects(
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search: Optional[str] = Query(None, max_length=255, description="Search query for name/description"),
    sort: str = Query(
        "-created_at",
        regex="^-?(created_at|updated_at|name)$",
        description="Sort field (prefix with - for descending)",
    ),
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    """
    List projects owned by the authenticated user.

    Args:
        limit: Maximum number of results (1-100)
        offset: Pagination offset
        search: Optional search query for name or description
        sort: Sort field with optional - prefix for descending order
        user_info: Authenticated user information from JWT
        db: Database session

    Returns:
        Paginated list of projects with total count

    Raises:
        HTTPException: If query fails
    """
    user_id = UUID(user_info.get("sub"))

    # Parse sort parameter
    sort_desc = sort.startswith("-")
    sort_by = sort.lstrip("-")

    logger.info(
        "Listing projects",
        user_id=str(user_id),
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    try:
        service = ProjectService(db)
        projects, total = await service.list_projects(
            user_id=user_id,
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

        logger.info(
            "Projects listed successfully",
            user_id=str(user_id),
            count=len(projects),
            total=total,
        )

        return ProjectListResponse(
            total=total,
            limit=limit,
            offset=offset,
            projects=[ProjectResponse.model_validate(p) for p in projects],
        )

    except Exception as e:
        logger.error(
            "Error listing projects",
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects",
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Get a specific project by ID. User must be the owner.",
)
async def get_project(
    project_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Get a specific project by ID.

    Args:
        project_id: Project UUID
        user_info: Authenticated user information from JWT
        db: Database session

    Returns:
        Project details

    Raises:
        HTTPException: If project not found or user lacks permission
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Getting project",
        project_id=str(project_id),
        user_id=str(user_id),
    )

    try:
        service = ProjectService(db)

        # Check ownership
        if not await service.check_owner_permission(project_id, user_id):
            logger.warning(
                "Unauthorized project access attempt",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        project = await service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        logger.info(
            "Project retrieved successfully",
            project_id=str(project_id),
            user_id=str(user_id),
        )

        return ProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting project",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get project",
        )


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update project fields. User must be the owner. Supports partial updates.",
)
async def update_project(
    project_id: UUID,
    update_data: ProjectUpdate,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Update project fields.

    Args:
        project_id: Project UUID
        update_data: Fields to update (all optional)
        user_info: Authenticated user information from JWT
        db: Database session

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found, user lacks permission, or update fails
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Updating project",
        project_id=str(project_id),
        user_id=str(user_id),
    )

    try:
        service = ProjectService(db)

        # Check ownership
        if not await service.check_owner_permission(project_id, user_id):
            logger.warning(
                "Unauthorized project update attempt",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        project = await service.update_project(project_id, update_data)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        logger.info(
            "Project updated successfully",
            project_id=str(project_id),
            user_id=str(user_id),
        )

        return ProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "Invalid project update data",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid update data: {str(e)}",
        )
    except Exception as e:
        logger.error(
            "Error updating project",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project",
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project. User must be the owner. This action cannot be undone.",
)
async def delete_project(
    project_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a project.

    Args:
        project_id: Project UUID
        user_info: Authenticated user information from JWT
        db: Database session

    Raises:
        HTTPException: If project not found or user lacks permission
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Deleting project",
        project_id=str(project_id),
        user_id=str(user_id),
    )

    try:
        service = ProjectService(db)

        # Check ownership
        if not await service.check_owner_permission(project_id, user_id):
            logger.warning(
                "Unauthorized project deletion attempt",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        deleted = await service.delete_project(project_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        logger.info(
            "Project deleted successfully",
            project_id=str(project_id),
            user_id=str(user_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting project",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project",
        )
