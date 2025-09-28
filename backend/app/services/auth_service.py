"""Authentication service for NextAuth.js database operations."""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

import structlog
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, Account, Session, VerificationToken
from app.core.auth import create_jwt_token

logger = structlog.get_logger(__name__)


class AuthService:
    """Service for authentication and session management operations."""

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        name: Optional[str] = None,
        image: Optional[str] = None,
        email_verified: Optional[datetime] = None,
        **kwargs
    ) -> User:
        """Create a new user with NextAuth.js compatibility."""
        user = User(
            email=email,
            name=name,
            image=image,
            email_verified=email_verified,
            **kwargs
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info("User created", user_id=str(user.id), email=user.email)
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID with all related data."""
        stmt = (
            select(User)
            .options(
                selectinload(User.accounts),
                selectinload(User.sessions)
            )
            .where(User.id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email address."""
        stmt = (
            select(User)
            .options(
                selectinload(User.accounts),
                selectinload(User.sessions)
            )
            .where(User.email == email)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[User]:
        """Update user with provided data."""
        user = await AuthService.get_user_by_id(db, user_id)
        if not user:
            return None

        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

        logger.info("User updated", user_id=str(user.id), updates=list(updates.keys()))
        return user

    @staticmethod
    async def create_account(
        db: AsyncSession,
        user_id: UUID,
        provider: str,
        provider_account_id: str,
        account_type: str = "oauth",
        **token_data
    ) -> Account:
        """Create OAuth account for user."""
        account = Account(
            user_id=user_id,
            type=account_type,
            provider=provider,
            provider_account_id=provider_account_id,
            **token_data
        )

        db.add(account)
        await db.commit()
        await db.refresh(account)

        logger.info(
            "Account created",
            user_id=str(user_id),
            provider=provider,
            account_id=str(account.id)
        )
        return account

    @staticmethod
    async def get_account(
        db: AsyncSession,
        provider: str,
        provider_account_id: str
    ) -> Optional[Account]:
        """Get account by provider and provider account ID."""
        stmt = (
            select(Account)
            .options(selectinload(Account.user))
            .where(
                and_(
                    Account.provider == provider,
                    Account.provider_account_id == provider_account_id
                )
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_account(
        db: AsyncSession,
        account_id: UUID,
        **token_data
    ) -> Optional[Account]:
        """Update OAuth account token data."""
        stmt = select(Account).where(Account.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            return None

        for key, value in token_data.items():
            if hasattr(account, key):
                setattr(account, key, value)

        account.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(account)

        logger.info("Account updated", account_id=str(account.id))
        return account

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: UUID,
        session_token: str,
        expires: datetime
    ) -> Session:
        """Create a new user session."""
        session = Session(
            user_id=user_id,
            session_token=session_token,
            expires=expires
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info("Session created", user_id=str(user_id), session_id=str(session.id))
        return session

    @staticmethod
    async def get_session_by_token(
        db: AsyncSession,
        session_token: str
    ) -> Optional[Session]:
        """Get session by session token."""
        stmt = (
            select(Session)
            .options(selectinload(Session.user))
            .where(Session.session_token == session_token)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_session(
        db: AsyncSession,
        session_token: str,
        expires: datetime
    ) -> Optional[Session]:
        """Update session expiration."""
        stmt = select(Session).where(Session.session_token == session_token)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.expires = expires
        session.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)

        logger.info("Session updated", session_id=str(session.id))
        return session

    @staticmethod
    async def delete_session(db: AsyncSession, session_token: str) -> bool:
        """Delete session by token."""
        stmt = delete(Session).where(Session.session_token == session_token)
        result = await db.execute(stmt)
        await db.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info("Session deleted", session_token=session_token[:8] + "...")

        return deleted

    @staticmethod
    async def create_verification_token(
        db: AsyncSession,
        identifier: str,
        token: str,
        expires: datetime
    ) -> VerificationToken:
        """Create verification token for email verification."""
        verification_token = VerificationToken(
            identifier=identifier,
            token=token,
            expires=expires
        )

        db.add(verification_token)
        await db.commit()
        await db.refresh(verification_token)

        logger.info("Verification token created", identifier=identifier)
        return verification_token

    @staticmethod
    async def get_verification_token(
        db: AsyncSession,
        identifier: str,
        token: str
    ) -> Optional[VerificationToken]:
        """Get verification token."""
        stmt = select(VerificationToken).where(
            and_(
                VerificationToken.identifier == identifier,
                VerificationToken.token == token
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_verification_token(
        db: AsyncSession,
        identifier: str,
        token: str
    ) -> bool:
        """Delete verification token."""
        stmt = delete(VerificationToken).where(
            and_(
                VerificationToken.identifier == identifier,
                VerificationToken.token == token
            )
        )
        result = await db.execute(stmt)
        await db.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info("Verification token deleted", identifier=identifier)

        return deleted

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Clean up expired sessions."""
        now = datetime.now(timezone.utc)
        stmt = delete(Session).where(Session.expires < now)
        result = await db.execute(stmt)
        await db.commit()

        count = result.rowcount
        if count > 0:
            logger.info("Expired sessions cleaned up", count=count)

        return count

    @staticmethod
    async def cleanup_expired_verification_tokens(db: AsyncSession) -> int:
        """Clean up expired verification tokens."""
        now = datetime.now(timezone.utc)
        stmt = delete(VerificationToken).where(VerificationToken.expires < now)
        result = await db.execute(stmt)
        await db.commit()

        count = result.rowcount
        if count > 0:
            logger.info("Expired verification tokens cleaned up", count=count)

        return count

    @staticmethod
    async def get_user_sessions(db: AsyncSession, user_id: UUID) -> List[Session]:
        """Get all active sessions for a user."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(Session)
            .where(
                and_(
                    Session.user_id == user_id,
                    Session.expires > now
                )
            )
            .order_by(Session.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def revoke_all_user_sessions(db: AsyncSession, user_id: UUID) -> int:
        """Revoke all sessions for a user."""
        stmt = delete(Session).where(Session.user_id == user_id)
        result = await db.execute(stmt)
        await db.commit()

        count = result.rowcount
        logger.info("All user sessions revoked", user_id=str(user_id), count=count)
        return count