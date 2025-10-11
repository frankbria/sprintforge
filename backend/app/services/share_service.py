"""Share link service for public project sharing."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.models.share_link import ShareLink
from app.models.project import Project
from app.schemas.sharing import ShareLinkCreate, ShareLinkUpdate

logger = structlog.get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ShareService:
    """Service for managing share links."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_token() -> str:
        """Generate cryptographically secure URL-safe token.

        Returns:
            64-character URL-safe token
        """
        return secrets.token_urlsafe(48)  # 48 bytes = 64 chars in base64

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Bcrypt hash
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Bcrypt hash

        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    async def create_share_link(
        self,
        project_id: UUID,
        user_id: UUID,
        share_data: ShareLinkCreate,
        base_url: str = "https://sprintforge.com"
    ) -> ShareLink:
        """Create a new share link for a project.

        Args:
            project_id: Project UUID
            user_id: Creator user UUID
            share_data: Share link configuration
            base_url: Base URL for share links

        Returns:
            Created share link

        Raises:
            HTTPException: If project not found
        """
        # Verify project exists
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Generate unique token
        token = self.generate_token()

        # Calculate expiration date
        expires_at = None
        if share_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=share_data.expires_in_days)

        # Hash password if provided
        password_hash = None
        if share_data.password:
            password_hash = self.hash_password(share_data.password)

        # Create share link
        share_link = ShareLink(
            project_id=project_id,
            token=token,
            access_type=share_data.access_type,
            expires_at=expires_at,
            password_hash=password_hash,
            created_by=user_id
        )

        self.db.add(share_link)
        await self.db.commit()
        await self.db.refresh(share_link)

        logger.info(
            "Share link created",
            share_link_id=str(share_link.id),
            project_id=str(project_id),
            access_type=share_data.access_type,
            expires_at=expires_at.isoformat() if expires_at else None,
            password_protected=share_data.password is not None
        )

        return share_link

    async def get_share_link_by_token(self, token: str) -> Optional[ShareLink]:
        """Get share link by token.

        Args:
            token: Share link token

        Returns:
            ShareLink if found, None otherwise
        """
        result = await self.db.execute(
            select(ShareLink)
            .options(selectinload(ShareLink.project))
            .where(ShareLink.token == token)
        )
        return result.scalar_one_or_none()

    async def verify_share_access(
        self,
        token: str,
        password: Optional[str] = None
    ) -> tuple[ShareLink, Project]:
        """Verify access to a shared project.

        Args:
            token: Share link token
            password: Optional password for protected links

        Returns:
            Tuple of (ShareLink, Project)

        Raises:
            HTTPException: If link not found, expired, or password incorrect
        """
        share_link = await self.get_share_link_by_token(token)

        if not share_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found"
            )

        # Check expiration
        if share_link.is_expired():
            logger.warning(
                "Expired share link accessed",
                share_link_id=str(share_link.id),
                expires_at=share_link.expires_at.isoformat() if share_link.expires_at else None
            )
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Share link has expired"
            )

        # Check password
        if share_link.is_password_protected():
            if not password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Password required for this share link"
                )
            if not self.verify_password(password, share_link.password_hash):
                logger.warning(
                    "Incorrect password for share link",
                    share_link_id=str(share_link.id)
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password"
                )

        # Update access tracking
        share_link.access_count += 1
        share_link.last_accessed_at = datetime.utcnow()
        await self.db.commit()

        logger.info(
            "Share link accessed",
            share_link_id=str(share_link.id),
            project_id=str(share_link.project_id),
            access_count=share_link.access_count
        )

        return share_link, share_link.project

    async def list_project_share_links(self, project_id: UUID) -> List[ShareLink]:
        """List all share links for a project.

        Args:
            project_id: Project UUID

        Returns:
            List of share links
        """
        result = await self.db.execute(
            select(ShareLink)
            .where(ShareLink.project_id == project_id)
            .order_by(ShareLink.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_share_link(
        self,
        share_id: UUID,
        update_data: ShareLinkUpdate
    ) -> ShareLink:
        """Update a share link.

        Args:
            share_id: Share link UUID
            update_data: Update data

        Returns:
            Updated share link

        Raises:
            HTTPException: If share link not found
        """
        result = await self.db.execute(
            select(ShareLink).where(ShareLink.id == share_id)
        )
        share_link = result.scalar_one_or_none()

        if not share_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found"
            )

        # Update fields
        if update_data.access_type is not None:
            share_link.access_type = update_data.access_type

        if update_data.expires_at is not None:
            share_link.expires_at = update_data.expires_at

        if update_data.password is not None:
            if update_data.password == "":
                # Remove password
                share_link.password_hash = None
            else:
                # Update password
                share_link.password_hash = self.hash_password(update_data.password)

        await self.db.commit()
        await self.db.refresh(share_link)

        logger.info(
            "Share link updated",
            share_link_id=str(share_link.id),
            access_type=share_link.access_type
        )

        return share_link

    async def delete_share_link(self, share_id: UUID) -> bool:
        """Delete a share link.

        Args:
            share_id: Share link UUID

        Returns:
            True if deleted

        Raises:
            HTTPException: If share link not found
        """
        result = await self.db.execute(
            select(ShareLink).where(ShareLink.id == share_id)
        )
        share_link = result.scalar_one_or_none()

        if not share_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found"
            )

        await self.db.delete(share_link)
        await self.db.commit()

        logger.info(
            "Share link deleted",
            share_link_id=str(share_id),
            project_id=str(share_link.project_id)
        )

        return True

    async def get_share_link(self, share_id: UUID) -> ShareLink:
        """Get share link by ID.

        Args:
            share_id: Share link UUID

        Returns:
            ShareLink

        Raises:
            HTTPException: If not found
        """
        result = await self.db.execute(
            select(ShareLink).where(ShareLink.id == share_id)
        )
        share_link = result.scalar_one_or_none()

        if not share_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found"
            )

        return share_link
