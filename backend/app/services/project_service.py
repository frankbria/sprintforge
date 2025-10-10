"""Project service for business logic and database operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = structlog.get_logger(__name__)


class ProjectService:
    """Service for project CRUD operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def create_project(
        self,
        user_id: UUID,
        project_data: ProjectCreate
    ) -> Project:
        """
        Create a new project.

        Args:
            user_id: Owner user ID
            project_data: Project creation data

        Returns:
            Created Project model instance

        Raises:
            ValueError: If configuration is invalid
        """
        logger.info(
            "Creating project",
            user_id=str(user_id),
            project_name=project_data.name
        )

        # Ensure project_id in configuration matches
        config_dict = project_data.configuration.model_dump()
        if not config_dict.get("project_id"):
            config_dict["project_id"] = f"proj_{project_data.name.lower().replace(' ', '_')}"

        if not config_dict.get("project_name"):
            config_dict["project_name"] = project_data.name

        project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=user_id,
            configuration=config_dict,
            template_version="1.0",
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        logger.info(
            "Project created successfully",
            project_id=str(project.id),
            user_id=str(user_id)
        )

        return project

    async def get_project(self, project_id: UUID) -> Optional[Project]:
        """
        Get project by ID.

        Args:
            project_id: Project UUID

        Returns:
            Project if found, None otherwise
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[List[Project], int]:
        """
        List projects owned by user with pagination and filtering.

        Args:
            user_id: Owner user ID
            limit: Maximum number of results
            offset: Pagination offset
            search: Optional search query for name/description
            sort_by: Field to sort by (created_at, updated_at, name)
            sort_desc: Sort in descending order

        Returns:
            Tuple of (projects list, total count)
        """
        # Build base query
        query = select(Project).where(Project.owner_id == user_id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_pattern),
                    Project.description.ilike(search_pattern),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply sorting
        sort_field = getattr(Project, sort_by, Project.created_at)
        if sort_desc:
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        projects = list(result.scalars().all())

        logger.info(
            "Listed projects",
            user_id=str(user_id),
            count=len(projects),
            total=total
        )

        return projects, total

    async def update_project(
        self,
        project_id: UUID,
        update_data: ProjectUpdate
    ) -> Optional[Project]:
        """
        Update project fields.

        Args:
            project_id: Project UUID
            update_data: Fields to update

        Returns:
            Updated Project if found, None otherwise
        """
        project = await self.get_project(project_id)
        if not project:
            return None

        # Update fields that are provided
        update_dict = update_data.model_dump(exclude_unset=True)

        # Handle configuration partial updates
        if "configuration" in update_dict and update_dict["configuration"]:
            current_config = project.configuration or {}
            new_config = update_dict["configuration"]
            # Merge configurations (new values override old)
            merged_config = {**current_config, **new_config}
            project.configuration = merged_config
            del update_dict["configuration"]

        # Update other fields
        for field, value in update_dict.items():
            if hasattr(project, field):
                setattr(project, field, value)

        await self.db.commit()
        await self.db.refresh(project)

        logger.info(
            "Project updated",
            project_id=str(project_id),
            updated_fields=list(update_dict.keys())
        )

        return project

    async def delete_project(self, project_id: UUID) -> bool:
        """
        Delete project (soft delete for MVP, can add deleted_at later).

        Args:
            project_id: Project UUID

        Returns:
            True if deleted, False if not found
        """
        project = await self.get_project(project_id)
        if not project:
            return False

        await self.db.delete(project)
        await self.db.commit()

        logger.info(
            "Project deleted",
            project_id=str(project_id)
        )

        return True

    async def check_owner_permission(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Check if user is the project owner.

        Args:
            project_id: Project UUID
            user_id: User UUID

        Returns:
            True if user is owner, False otherwise
        """
        result = await self.db.execute(
            select(Project.id).where(
                Project.id == project_id,
                Project.owner_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None
