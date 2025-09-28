"""Tests for UserService profile management and synchronization."""

import pytest
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

# Set environment variables before importing app modules
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['CORS_ORIGINS'] = '["http://localhost:3000"]'

from app.services.user_service import UserService
from app.models.user import User, Account


class TestUserService:
    """Test UserService profile management operations."""

    @pytest.mark.asyncio
    async def test_sync_user_from_oauth_new_user(self):
        """Test syncing new user from OAuth profile."""
        db = AsyncMock()

        # Mock no existing account
        db.execute.return_value.scalar_one_or_none.side_effect = [None, None]

        oauth_profile = {
            "email": "newuser@example.com",
            "name": "New User",
            "image": "https://example.com/avatar.jpg",
            "email_verified": True
        }

        # Mock user creation
        with patch.object(
            UserService,
            '_create_user_from_oauth_profile',
            return_value=User(
                id=uuid4(),
                email=oauth_profile["email"],
                name=oauth_profile["name"]
            )
        ) as mock_create:
            result = await UserService.sync_user_from_oauth(
                db, "google", "google123", oauth_profile
            )

            assert result.email == oauth_profile["email"]
            assert result.name == oauth_profile["name"]
            mock_create.assert_called_once_with(db, oauth_profile)

    @pytest.mark.asyncio
    async def test_sync_user_from_oauth_existing_account(self):
        """Test syncing existing user from OAuth profile."""
        db = AsyncMock()

        user_id = uuid4()
        existing_user = User(
            id=user_id,
            email="existing@example.com",
            name="Old Name"
        )

        existing_account = Account(
            id=uuid4(),
            user_id=user_id,
            provider="google",
            provider_account_id="google123",
            user=existing_user
        )

        # Mock existing account found
        db.execute.return_value.scalar_one_or_none.return_value = existing_account

        oauth_profile = {
            "email": "existing@example.com",
            "name": "Updated Name",
            "image": "https://example.com/new-avatar.jpg"
        }

        # Mock profile update
        with patch.object(
            UserService,
            '_update_user_from_oauth_profile',
            return_value=["name", "image"]
        ) as mock_update:
            result = await UserService.sync_user_from_oauth(
                db, "google", "google123", oauth_profile
            )

            assert result == existing_user
            mock_update.assert_called_once_with(db, existing_user, oauth_profile)

    @pytest.mark.asyncio
    async def test_sync_user_from_oauth_link_existing_email(self):
        """Test linking OAuth account to existing user with same email."""
        db = AsyncMock()

        existing_user = User(
            id=uuid4(),
            email="existing@example.com",
            name="Existing User"
        )

        # Mock no existing account but existing user with same email
        db.execute.return_value.scalar_one_or_none.side_effect = [None, existing_user]

        oauth_profile = {
            "email": "existing@example.com",
            "name": "OAuth Name"
        }

        result = await UserService.sync_user_from_oauth(
            db, "microsoft", "ms456", oauth_profile
        )

        assert result == existing_user

    @pytest.mark.asyncio
    async def test_sync_user_from_oauth_missing_email(self):
        """Test syncing OAuth profile without email."""
        db = AsyncMock()

        oauth_profile = {
            "name": "No Email User",
            "image": "https://example.com/avatar.jpg"
        }

        with pytest.raises(ValueError, match="OAuth profile missing email address"):
            await UserService.sync_user_from_oauth(
                db, "google", "google123", oauth_profile
            )

    @pytest.mark.asyncio
    async def test_create_user_from_oauth_profile(self):
        """Test creating user from OAuth profile."""
        db = AsyncMock()

        oauth_profile = {
            "email": "oauth@example.com",
            "name": "OAuth User",
            "image": "https://example.com/avatar.jpg",
            "email_verified": True
        }

        # Mock user creation
        created_user = User(
            id=uuid4(),
            email=oauth_profile["email"],
            name=oauth_profile["name"],
            image=oauth_profile["image"],
            email_verified=datetime.now(timezone.utc)
        )

        db.add = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(return_value=created_user)

        result = await UserService._create_user_from_oauth_profile(db, oauth_profile)

        assert result.email == oauth_profile["email"]
        assert result.name == oauth_profile["name"]
        assert result.image == oauth_profile["image"]
        db.add.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_from_oauth_profile(self):
        """Test updating user with OAuth profile data."""
        db = AsyncMock()

        user = User(
            id=uuid4(),
            email="user@example.com",
            name="Short",
            image=None,
            email_verified=None
        )

        oauth_profile = {
            "name": "Much Longer OAuth Name",
            "image": "https://example.com/new-avatar.jpg",
            "email_verified": True
        }

        updated_fields = await UserService._update_user_from_oauth_profile(
            db, user, oauth_profile
        )

        assert "name" in updated_fields
        assert "image" in updated_fields
        assert "email_verified" in updated_fields
        assert user.name == "Much Longer OAuth Name"
        assert user.image == "https://example.com/new-avatar.jpg"
        assert user.email_verified is not None
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_from_oauth_profile_no_changes(self):
        """Test updating user when OAuth profile provides no new data."""
        db = AsyncMock()

        user = User(
            id=uuid4(),
            email="user@example.com",
            name="Existing Long Name",
            image="https://example.com/existing.jpg",
            email_verified=datetime.now(timezone.utc)
        )

        oauth_profile = {
            "name": "Short",  # Shorter than existing
            "image": "https://example.com/existing.jpg",  # Same as existing
            "email_verified": True  # Already verified
        }

        updated_fields = await UserService._update_user_from_oauth_profile(
            db, user, oauth_profile
        )

        assert len(updated_fields) == 0
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_profile(self):
        """Test updating user profile with validated data."""
        db = AsyncMock()
        user_id = uuid4()

        user = User(
            id=user_id,
            email="user@example.com",
            name="Old Name",
            preferences={"theme": "dark"}
        )

        db.execute.return_value.scalar_one_or_none.return_value = user

        profile_data = {
            "name": "New Name",
            "preferences": {"theme": "light", "language": "es"},
            "email": "hacker@evil.com"  # Should be ignored (not in allowed_fields)
        }

        result = await UserService.update_user_profile(db, user_id, profile_data)

        assert result == user
        assert user.name == "New Name"
        assert user.preferences == {"theme": "light", "language": "es"}
        assert user.email == "user@example.com"  # Unchanged
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self):
        """Test updating profile for non-existent user."""
        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none.return_value = None

        result = await UserService.update_user_profile(
            db, uuid4(), {"name": "New Name"}
        )

        assert result is None
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_preferences(self):
        """Test updating user preferences."""
        db = AsyncMock()
        user_id = uuid4()

        user = User(
            id=user_id,
            email="user@example.com",
            preferences={"theme": "dark", "notifications": True}
        )

        db.execute.return_value.scalar_one_or_none.return_value = user

        new_preferences = {"theme": "light", "language": "fr"}

        result = await UserService.update_user_preferences(db, user_id, new_preferences)

        assert result == user
        # Should merge with existing preferences
        expected_prefs = {
            "theme": "light",  # Updated
            "notifications": True,  # Preserved
            "language": "fr"  # Added
        }
        assert user.preferences == expected_prefs
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_preferences_empty_existing(self):
        """Test updating preferences when user has no existing preferences."""
        db = AsyncMock()
        user_id = uuid4()

        user = User(
            id=user_id,
            email="user@example.com",
            preferences=None
        )

        db.execute.return_value.scalar_one_or_none.return_value = user

        new_preferences = {"theme": "light"}

        result = await UserService.update_user_preferences(db, user_id, new_preferences)

        assert result == user
        assert user.preferences == {"theme": "light"}

    @pytest.mark.asyncio
    async def test_get_user_with_accounts(self):
        """Test getting user with linked accounts."""
        db = AsyncMock()
        user_id = uuid4()

        mock_user = User(id=user_id, email="user@example.com")
        db.execute.return_value.scalar_one_or_none.return_value = mock_user

        result = await UserService.get_user_with_accounts(db, user_id)

        assert result == mock_user
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_statistics(self):
        """Test getting user statistics."""
        db = AsyncMock()
        user_id = uuid4()

        user = User(
            id=user_id,
            email="stats@example.com",
            name="Stats User",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            subscription_tier="pro",
            subscription_status="active",
            email_verified=datetime.now(timezone.utc),
            image="https://example.com/avatar.jpg",
            preferences={"theme": "dark", "notifications": True}
        )

        # Mock accounts
        user.accounts = [
            Account(provider="google"),
            Account(provider="microsoft")
        ]

        # Mock get_user_with_accounts
        with patch.object(
            UserService,
            'get_user_with_accounts',
            return_value=user
        ):
            # Mock get_user_sessions from AuthService
            with patch('app.services.user_service.AuthService.get_user_sessions') as mock_sessions:
                mock_sessions.return_value = ["session1", "session2"]

                stats = await UserService.get_user_statistics(db, user_id)

                assert stats["user_id"] == str(user_id)
                assert stats["email"] == "stats@example.com"
                assert stats["subscription_tier"] == "pro"
                assert stats["linked_accounts"] == 2
                assert stats["oauth_providers"] == ["google", "microsoft"]
                assert stats["active_sessions"] == 2
                assert stats["email_verified"] is True
                assert stats["has_profile_image"] is True
                assert stats["preferences_set"] == 2

    @pytest.mark.asyncio
    async def test_get_user_statistics_not_found(self):
        """Test getting statistics for non-existent user."""
        db = AsyncMock()

        with patch.object(
            UserService,
            'get_user_with_accounts',
            return_value=None
        ):
            stats = await UserService.get_user_statistics(db, uuid4())
            assert stats == {}

    @pytest.mark.asyncio
    async def test_deactivate_user(self):
        """Test user account deactivation."""
        db = AsyncMock()
        user_id = uuid4()

        user = User(
            id=user_id,
            email="deactivate@example.com",
            is_active=True,
            preferences={"theme": "dark"}
        )

        db.execute.return_value.scalar_one_or_none.return_value = user

        # Mock revoke_all_user_sessions from AuthService
        with patch('app.services.user_service.AuthService.revoke_all_user_sessions') as mock_revoke:
            mock_revoke.return_value = 2

            result = await UserService.deactivate_user(db, user_id, "user_request")

            assert result is True
            assert user.is_active is False
            assert "deactivation_reason" in user.preferences
            assert user.preferences["deactivation_reason"] == "user_request"
            assert "deactivated_at" in user.preferences
            mock_revoke.assert_called_once_with(db, user_id)

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self):
        """Test deactivating non-existent user."""
        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none.return_value = None

        result = await UserService.deactivate_user(db, uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_reactivate_user(self):
        """Test user account reactivation."""
        db = AsyncMock()
        user_id = uuid4()

        user = User(
            id=user_id,
            email="reactivate@example.com",
            is_active=False,
            preferences={
                "theme": "dark",
                "deactivation_reason": "user_request",
                "deactivated_at": "2023-01-01T00:00:00"
            }
        )

        db.execute.return_value.scalar_one_or_none.return_value = user

        result = await UserService.reactivate_user(db, user_id)

        assert result is True
        assert user.is_active is True
        assert "deactivation_reason" not in user.preferences
        assert "deactivated_at" not in user.preferences
        assert user.preferences == {"theme": "dark"}

    @pytest.mark.asyncio
    async def test_search_users(self):
        """Test searching users by email or name."""
        db = AsyncMock()

        mock_users = [
            User(id=uuid4(), email="john@example.com", name="John Doe"),
            User(id=uuid4(), email="jane@example.com", name="Jane Smith")
        ]

        db.execute.return_value.scalars.return_value.all.return_value = mock_users

        result = await UserService.search_users(db, "john", limit=10)

        assert len(result) == 2
        assert result == mock_users
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_users(self):
        """Test getting recently registered users."""
        db = AsyncMock()

        recent_date = datetime.now(timezone.utc) - timedelta(days=15)
        mock_users = [
            User(id=uuid4(), email="recent1@example.com", created_at=recent_date),
            User(id=uuid4(), email="recent2@example.com", created_at=recent_date)
        ]

        db.execute.return_value.scalars.return_value.all.return_value = mock_users

        result = await UserService.get_recent_users(db, days=30, limit=50)

        assert len(result) == 2
        assert result == mock_users
        db.execute.assert_called_once()


class TestUserServiceErrorHandling:
    """Test error handling in UserService."""

    @pytest.mark.asyncio
    async def test_update_user_profile_no_allowed_fields(self):
        """Test updating user profile with no allowed fields."""
        db = AsyncMock()
        user_id = uuid4()

        user = User(
            id=user_id,
            email="user@example.com"
        )

        db.execute.return_value.scalar_one_or_none.return_value = user

        # Only provide disallowed fields
        profile_data = {
            "email": "hacker@evil.com",
            "id": uuid4(),
            "created_at": datetime.now(timezone.utc)
        }

        result = await UserService.update_user_profile(db, user_id, profile_data)

        assert result == user
        # No changes should be made
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_reactivate_user_with_no_preferences(self):
        """Test reactivating user with no existing preferences."""
        db = AsyncMock()
        user_id = uuid4()

        user = User(
            id=user_id,
            email="reactivate@example.com",
            is_active=False,
            preferences=None
        )

        db.execute.return_value.scalar_one_or_none.return_value = user

        result = await UserService.reactivate_user(db, user_id)

        assert result is True
        assert user.is_active is True
        # Should not crash even with None preferences