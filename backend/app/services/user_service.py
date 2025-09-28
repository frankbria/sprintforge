"""User service for profile management and synchronization."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID

import structlog
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, Account

# Fix missing import for timedelta
from datetime import timedelta

logger = structlog.get_logger(__name__)


class UserService:
    """Service for user profile management and OAuth synchronization."""

    @staticmethod
    async def sync_user_from_oauth(
        db: AsyncSession,
        provider: str,
        provider_account_id: str,
        oauth_profile: Dict[str, Any]
    ) -> User:
        """Synchronize user profile from OAuth provider data."""
        # Try to find existing account
        account = await db.execute(
            select(Account)
            .options(selectinload(Account.user))
            .where(
                and_(
                    Account.provider == provider,
                    Account.provider_account_id == provider_account_id
                )
            )
        )
        existing_account = account.scalar_one_or_none()

        if existing_account:
            # Update existing user profile with latest OAuth data
            user = existing_account.user
            updated = await UserService._update_user_from_oauth_profile(
                db, user, oauth_profile
            )
            logger.info(
                "User profile synchronized from OAuth",
                user_id=str(user.id),
                provider=provider,
                updated_fields=updated
            )
        else:
            # Try to find user by email to link accounts
            email = oauth_profile.get("email")
            if email:
                result = await db.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()

                if user:
                    # Link existing user to new OAuth account
                    logger.info(
                        "Linking existing user to new OAuth account",
                        user_id=str(user.id),
                        provider=provider
                    )
                else:
                    # Create new user from OAuth profile
                    user = await UserService._create_user_from_oauth_profile(
                        db, oauth_profile
                    )
                    logger.info(
                        "Created new user from OAuth profile",
                        user_id=str(user.id),
                        provider=provider
                    )
            else:
                raise ValueError("OAuth profile missing email address")

        return user

    @staticmethod
    async def _create_user_from_oauth_profile(
        db: AsyncSession,
        oauth_profile: Dict[str, Any]
    ) -> User:
        """Create new user from OAuth profile data."""
        user_data = {
            "email": oauth_profile.get("email"),
            "name": oauth_profile.get("name"),
            "image": oauth_profile.get("image") or oauth_profile.get("picture"),
            "email_verified": datetime.now(timezone.utc) if oauth_profile.get("email_verified") else None,
            "preferences": {
                "theme": "light",
                "notifications": True,
                "timezone": "UTC",
                "language": "en"
            }
        }

        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}

        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def _update_user_from_oauth_profile(
        db: AsyncSession,
        user: User,
        oauth_profile: Dict[str, Any]
    ) -> List[str]:
        """Update existing user with OAuth profile data."""
        updated_fields = []

        # Update name if OAuth provides a more complete name
        oauth_name = oauth_profile.get("name")
        if oauth_name and (not user.name or len(oauth_name) > len(user.name or "")):
            user.name = oauth_name
            updated_fields.append("name")

        # Update image if OAuth provides one and user doesn't have one
        oauth_image = oauth_profile.get("image") or oauth_profile.get("picture")
        if oauth_image and not user.image:
            user.image = oauth_image
            updated_fields.append("image")

        # Update email verification if OAuth confirms it
        if oauth_profile.get("email_verified") and not user.email_verified:
            user.email_verified = datetime.now(timezone.utc)
            updated_fields.append("email_verified")

        if updated_fields:
            user.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(user)

        return updated_fields

    @staticmethod
    async def update_user_profile(
        db: AsyncSession,
        user_id: UUID,
        profile_data: Dict[str, Any]
    ) -> Optional[User]:
        """Update user profile with validated data."""
        user = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()

        if not user:
            return None

        # List of allowed fields that can be updated
        allowed_fields = {"name", "image", "preferences"}
        updated_fields = []

        for field, value in profile_data.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
                updated_fields.append(field)

        if updated_fields:
            user.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(user)

            logger.info(
                "User profile updated",
                user_id=str(user.id),
                updated_fields=updated_fields
            )

        return user

    @staticmethod
    async def update_user_preferences(
        db: AsyncSession,
        user_id: UUID,
        preferences: Dict[str, Any]
    ) -> Optional[User]:
        """Update user preferences (merge with existing)."""
        user = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()

        if not user:
            return None

        # Merge with existing preferences
        current_prefs = user.preferences or {}
        current_prefs.update(preferences)
        user.preferences = current_prefs
        user.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(user)

        logger.info(
            "User preferences updated",
            user_id=str(user.id),
            preferences=list(preferences.keys())
        )

        return user

    @staticmethod
    async def get_user_with_accounts(
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[User]:
        """Get user with all linked OAuth accounts."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.accounts))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_statistics(
        db: AsyncSession,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get user usage statistics and account info."""
        user = await UserService.get_user_with_accounts(db, user_id)
        if not user:
            return {}

        # Count linked accounts
        account_count = len(user.accounts)
        providers = [account.provider for account in user.accounts]

        # Count active sessions
        from app.services.auth_service import AuthService
        sessions = await AuthService.get_user_sessions(db, user_id)
        active_sessions = len(sessions)

        return {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at,
            "last_updated": user.updated_at,
            "subscription_tier": user.subscription_tier,
            "subscription_status": user.subscription_status,
            "linked_accounts": account_count,
            "oauth_providers": providers,
            "active_sessions": active_sessions,
            "email_verified": user.email_verified is not None,
            "has_profile_image": user.image is not None,
            "preferences_set": len(user.preferences or {})
        }

    @staticmethod
    async def deactivate_user(
        db: AsyncSession,
        user_id: UUID,
        reason: str = "user_request"
    ) -> bool:
        """Deactivate user account (soft delete)."""
        user = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()

        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)

        # Add deactivation reason to preferences
        if not user.preferences:
            user.preferences = {}
        user.preferences["deactivation_reason"] = reason
        user.preferences["deactivated_at"] = datetime.now(timezone.utc).isoformat()

        await db.commit()

        # Revoke all sessions
        from app.services.auth_service import AuthService
        await AuthService.revoke_all_user_sessions(db, user_id)

        logger.info(
            "User account deactivated",
            user_id=str(user.id),
            reason=reason
        )

        return True

    @staticmethod
    async def reactivate_user(
        db: AsyncSession,
        user_id: UUID
    ) -> bool:
        """Reactivate user account."""
        user = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()

        if not user:
            return False

        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)

        # Remove deactivation info from preferences
        if user.preferences:
            user.preferences.pop("deactivation_reason", None)
            user.preferences.pop("deactivated_at", None)

        await db.commit()

        logger.info("User account reactivated", user_id=str(user.id))

        return True

    @staticmethod
    async def search_users(
        db: AsyncSession,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[User]:
        """Search users by email or name (admin function)."""
        search_term = f"%{query.lower()}%"

        stmt = (
            select(User)
            .where(
                and_(
                    User.is_active == True,
                    or_(
                        func.lower(User.email).like(search_term),
                        func.lower(User.name).like(search_term)
                    )
                )
            )
            .limit(limit)
            .offset(offset)
            .order_by(User.created_at.desc())
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_recent_users(
        db: AsyncSession,
        days: int = 30,
        limit: int = 100
    ) -> List[User]:
        """Get recently registered users."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(User)
            .where(
                and_(
                    User.is_active == True,
                    User.created_at >= cutoff_date
                )
            )
            .limit(limit)
            .order_by(User.created_at.desc())
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())