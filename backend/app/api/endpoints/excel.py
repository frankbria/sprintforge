"""Excel generation API endpoints."""

from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.auth import require_auth
from app.database.connection import get_db
from app.services.project_service import ProjectService
from app.services.excel_service import ExcelService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["excel"])


@router.post(
    "/{project_id}/generate",
    summary="Generate Excel template",
    description="Generate Excel template for a project. Returns Excel file as streaming response.",
)
async def generate_excel(
    project_id: UUID,
    user_info: Dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Generate Excel template for a project.

    Args:
        project_id: Project UUID
        user_info: Authenticated user information from JWT
        db: Database session

    Returns:
        Excel file as streaming response

    Raises:
        HTTPException: If project not found, user lacks permission, or generation fails
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Excel generation requested",
        project_id=str(project_id),
        user_id=str(user_id),
    )

    try:
        project_service = ProjectService(db)

        # Check ownership
        if not await project_service.check_owner_permission(project_id, user_id):
            logger.warning(
                "Unauthorized Excel generation attempt",
                project_id=str(project_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Get project
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Generate Excel
        excel_service = ExcelService(db)
        excel_bytes = await excel_service.generate_excel(project)

        # Get filename
        filename = excel_service.get_filename(project)

        logger.info(
            "Excel generated successfully",
            project_id=str(project_id),
            user_id=str(user_id),
            filename=filename,
            size_bytes=len(excel_bytes),
        )

        # Return as streaming response
        from io import BytesIO

        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "Invalid project configuration for Excel generation",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project configuration: {str(e)}",
        )
    except Exception as e:
        logger.error(
            "Error generating Excel",
            project_id=str(project_id),
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Excel template",
        )
