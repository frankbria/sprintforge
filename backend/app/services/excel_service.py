"""Excel generation service for integrating with the Excel Template Engine."""

from datetime import datetime, timezone
from typing import Dict, Any
from uuid import UUID
from io import BytesIO

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.excel.engine import ExcelTemplateEngine, ProjectConfig
from app.models.project import Project

logger = structlog.get_logger(__name__)


class ExcelService:
    """Service for Excel template generation."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
        self.engine = ExcelTemplateEngine()

    def _map_project_to_config(self, project: Project) -> ProjectConfig:
        """
        Map database Project model to Excel ProjectConfig.

        Args:
            project: Database Project model

        Returns:
            ProjectConfig for Excel generation
        """
        config_data = project.configuration or {}

        # Create ProjectConfig for Excel engine
        return ProjectConfig(
            project_id=config_data.get("project_id", f"proj_{project.id}"),
            project_name=config_data.get("project_name", project.name),
            sprint_pattern=config_data.get("sprint_pattern", "YY.Q.#"),
            features=config_data.get("features", {}),
            metadata={
                "template_id": config_data.get("template_id", "default"),
                "description": project.description,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "owner_id": str(project.owner_id),
            },
        )

    async def generate_excel(self, project: Project) -> bytes:
        """
        Generate Excel template for a project.

        Args:
            project: Project model to generate template for

        Returns:
            Excel file content as bytes

        Raises:
            ValueError: If project configuration is invalid
        """
        logger.info(
            "Generating Excel template",
            project_id=str(project.id),
            project_name=project.name,
        )

        try:
            # Map project to Excel config
            config = self._map_project_to_config(project)

            # Generate Excel template
            excel_bytes = self.engine.generate_template(config)

            # Update last_generated_at timestamp
            project.last_generated_at = datetime.now(timezone.utc)
            await self.db.commit()

            logger.info(
                "Excel template generated successfully",
                project_id=str(project.id),
                size_bytes=len(excel_bytes),
            )

            return excel_bytes

        except Exception as e:
            logger.error(
                "Error generating Excel template",
                project_id=str(project.id),
                error=str(e),
            )
            raise

    def get_filename(self, project: Project) -> str:
        """
        Generate filename for Excel download.

        Args:
            project: Project model

        Returns:
            Safe filename with project name and date
        """
        # Sanitize project name for filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in project.name)
        safe_name = safe_name.replace(' ', '_')[:50]  # Limit length

        # Add date
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        return f"{safe_name}_{date_str}.xlsx"
