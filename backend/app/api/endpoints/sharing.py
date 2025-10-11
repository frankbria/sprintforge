"""Sharing API endpoints."""

from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.auth import require_auth, optional_auth
from app.database.connection import get_db
from app.schemas.sharing import (
    ShareLinkCreate,
    ShareLinkUpdate,
    ShareLinkResponse,
    ShareLinkListResponse,
    PublicProjectResponse,
    ShareAccessRequest
)
from app.services.share_service import ShareService
from app.services.project_service import ProjectService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["sharing"])


@router.post(
    "/projects/{project_id}/share",
    response_model=ShareLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create share link",
    description="Create a shareable link for a project with access control and optional password protection.",
    responses={
        201: {"description": "Share link created successfully"},
        403: {"description": "Forbidden - Not project owner"},
        404: {"description": "Project not found"},
        500: {"description": "Internal server error"},
    },
)
async def create_share_link(
    project_id: UUID,
    share_data: ShareLinkCreate,
    request: Request,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> ShareLinkResponse:
    """
    Create a share link for a project.

    **Access Control:**
    - Only project owners can create share links
    - Share links can have viewer, editor, or commenter access
    - Optional password protection
    - Optional expiration date (1-365 days)

    Args:
        project_id: Project UUID
        share_data: Share link configuration
        request: FastAPI request for base URL
        user_info: Authenticated user information from JWT
        db: Database session

    Returns:
        Created share link with shareable URL

    Raises:
        HTTPException: If not owner, project not found, or creation fails
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Creating share link",
        project_id=str(project_id),
        user_id=str(user_id),
        access_type=share_data.access_type,
    )

    try:
        # Check ownership
        project_service = ProjectService(db)
        if not await project_service.check_owner_permission(project_id, user_id):
            logger.warning(
                "Unauthorized share link creation attempt",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners can create share links",
            )

        # Create share link
        share_service = ShareService(db)
        base_url = str(request.base_url).rstrip("/")
        share_link = await share_service.create_share_link(
            project_id, user_id, share_data, base_url
        )

        # Build response with share URL
        response = ShareLinkResponse.model_validate(share_link)
        response.share_url = f"{base_url}/s/{share_link.token}"
        response.password_protected = share_link.is_password_protected()

        logger.info(
            "Share link created successfully",
            share_link_id=str(share_link.id),
            project_id=str(project_id),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating share link",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share link",
        )


@router.get(
    "/share/{token}",
    response_model=PublicProjectResponse,
    summary="Access shared project",
    description="Access a publicly shared project using a share link token. No authentication required.",
    responses={
        200: {"description": "Project accessed successfully"},
        401: {"description": "Unauthorized - Password required or incorrect"},
        404: {"description": "Share link not found"},
        410: {"description": "Gone - Share link has expired"},
        500: {"description": "Internal server error"},
    },
)
async def get_shared_project(
    token: str,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> PublicProjectResponse:
    """
    Access a publicly shared project.

    **No authentication required** - anyone with the link can access.

    **Password Protection:**
    - If link is password protected, password parameter is required
    - Returns 401 if password is incorrect or missing

    **Expiration:**
    - Returns 410 Gone if link has expired
    - Access count is incremented on successful access

    Args:
        token: Share link token from URL
        password: Optional password for protected links
        db: Database session

    Returns:
        Public project information with access permissions

    Raises:
        HTTPException: If link not found, expired, or password incorrect
    """
    logger.info(
        "Accessing shared project",
        token=token[:8] + "...",
        has_password=password is not None,
    )

    try:
        share_service = ShareService(db)
        share_link, project = await share_service.verify_share_access(token, password)

        # Build permissions based on access type
        can_generate = share_link.access_type in ["viewer", "editor"]
        can_edit = share_link.access_type == "editor"
        can_comment = share_link.access_type in ["editor", "commenter"]

        # Return public project data (sensitive fields excluded)
        response = PublicProjectResponse(
            project={
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "template_version": project.template_version,
                "created_at": project.created_at.isoformat(),
                "last_generated_at": project.last_generated_at.isoformat() if project.last_generated_at else None,
            },
            access_type=share_link.access_type,
            can_generate_excel=can_generate,
            can_edit=can_edit,
            can_comment=can_comment,
        )

        logger.info(
            "Shared project accessed successfully",
            share_link_id=str(share_link.id),
            project_id=str(project.id),
            access_type=share_link.access_type,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error accessing shared project",
            token=token[:8] + "...",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access shared project",
        )


@router.get(
    "/projects/{project_id}/shares",
    response_model=ShareLinkListResponse,
    summary="List project share links",
    description="List all share links for a project. Only accessible by project owner.",
    responses={
        200: {"description": "Share links retrieved successfully"},
        403: {"description": "Forbidden - Not project owner"},
        404: {"description": "Project not found"},
        500: {"description": "Internal server error"},
    },
)
async def list_project_shares(
    project_id: UUID,
    request: Request,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> ShareLinkListResponse:
    """
    List all share links for a project.

    **Access Control:**
    - Only project owners can list share links

    Args:
        project_id: Project UUID
        request: FastAPI request for base URL
        user_info: Authenticated user information from JWT
        db: Database session

    Returns:
        List of all share links for the project

    Raises:
        HTTPException: If not owner, project not found, or query fails
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Listing project share links",
        project_id=str(project_id),
        user_id=str(user_id),
    )

    try:
        # Check ownership
        project_service = ProjectService(db)
        if not await project_service.check_owner_permission(project_id, user_id):
            logger.warning(
                "Unauthorized share links list attempt",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners can list share links",
            )

        # Get share links
        share_service = ShareService(db)
        share_links = await share_service.list_project_share_links(project_id)

        # Build responses
        base_url = str(request.base_url).rstrip("/")
        responses = []
        for link in share_links:
            response = ShareLinkResponse.model_validate(link)
            response.share_url = f"{base_url}/s/{link.token}"
            response.password_protected = link.is_password_protected()
            responses.append(response)

        logger.info(
            "Share links listed successfully",
            project_id=str(project_id),
            count=len(responses),
        )

        return ShareLinkListResponse(
            total=len(responses),
            share_links=responses
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error listing share links",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list share links",
        )


@router.patch(
    "/shares/{share_id}",
    response_model=ShareLinkResponse,
    summary="Update share link",
    description="Update share link settings (access type, expiration, password).",
    responses={
        200: {"description": "Share link updated successfully"},
        403: {"description": "Forbidden - Not project owner"},
        404: {"description": "Share link not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_share_link(
    share_id: UUID,
    update_data: ShareLinkUpdate,
    request: Request,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> ShareLinkResponse:
    """
    Update a share link.

    **Access Control:**
    - Only project owners can update share links

    **Updatable Fields:**
    - access_type: Change access level
    - expires_at: Update expiration date
    - password: Update or remove password (empty string removes)

    Args:
        share_id: Share link UUID
        update_data: Update data
        request: FastAPI request for base URL
        user_info: Authenticated user information from JWT
        db: Database session

    Returns:
        Updated share link

    Raises:
        HTTPException: If not owner, link not found, or update fails
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Updating share link",
        share_id=str(share_id),
        user_id=str(user_id),
    )

    try:
        share_service = ShareService(db)

        # Get share link and check ownership
        share_link = await share_service.get_share_link(share_id)

        project_service = ProjectService(db)
        if not await project_service.check_owner_permission(share_link.project_id, user_id):
            logger.warning(
                "Unauthorized share link update attempt",
                share_id=str(share_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners can update share links",
            )

        # Update share link
        updated_link = await share_service.update_share_link(share_id, update_data)

        # Build response
        base_url = str(request.base_url).rstrip("/")
        response = ShareLinkResponse.model_validate(updated_link)
        response.share_url = f"{base_url}/s/{updated_link.token}"
        response.password_protected = updated_link.is_password_protected()

        logger.info(
            "Share link updated successfully",
            share_id=str(share_id),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating share link",
            share_id=str(share_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update share link",
        )


@router.delete(
    "/shares/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete share link",
    description="Delete (revoke) a share link. This action cannot be undone.",
    responses={
        204: {"description": "Share link deleted successfully"},
        403: {"description": "Forbidden - Not project owner"},
        404: {"description": "Share link not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_share_link(
    share_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete (revoke) a share link.

    **Access Control:**
    - Only project owners can delete share links

    **Effect:**
    - Share link becomes immediately inaccessible
    - Existing users with the link will receive 404 errors

    Args:
        share_id: Share link UUID
        user_info: Authenticated user information from JWT
        db: Database session

    Raises:
        HTTPException: If not owner, link not found, or deletion fails
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Deleting share link",
        share_id=str(share_id),
        user_id=str(user_id),
    )

    try:
        share_service = ShareService(db)

        # Get share link and check ownership
        share_link = await share_service.get_share_link(share_id)

        project_service = ProjectService(db)
        if not await project_service.check_owner_permission(share_link.project_id, user_id):
            logger.warning(
                "Unauthorized share link deletion attempt",
                share_id=str(share_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners can delete share links",
            )

        # Delete share link
        await share_service.delete_share_link(share_id)

        logger.info(
            "Share link deleted successfully",
            share_id=str(share_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting share link",
            share_id=str(share_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete share link",
        )
