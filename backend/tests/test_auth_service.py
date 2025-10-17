"""Tests for AuthService database operations."""

import pytest
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment variables before importing app modules
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['CORS_ORIGINS'] = '["http://localhost:3000"]'

from app.services.auth_service import AuthService
from app.models.user import User, Account, Session, VerificationToken


class TestAuthService:
    """Test AuthService database operations."""

    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test user creation."""
        db = AsyncMock()

        email = "test@example.com"
        name = "Test User"
        image = "https://example.com/avatar.jpg"

        user = await AuthService.create_user(
            db, email=email, name=name, image=image
        )

        assert user.email == email
        assert user.name == name
        assert user.image == image
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id(self):
        """Test getting user by ID."""
        db = AsyncMock()
        user_id = uuid4()

        mock_user = User(
            id=user_id,
            email="test@example.com",
            name="Test User"
        )

        # Create async mock for execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        db.execute.return_value = mock_result

        result = await AuthService.get_user_by_id(db, user_id)

        assert result == mock_user
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email(self):
        """Test getting user by email."""
        db = AsyncMock()
        email = "test@example.com"

        mock_user = User(
            id=uuid4(),
            email=email,
            name="Test User"
        )

        # Create async mock for execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        db.execute.return_value = mock_result

        result = await AuthService.get_user_by_email(db, email)

        assert result == mock_user
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user(self):
        """Test user update."""
        db = AsyncMock()
        user_id = uuid4()

        mock_user = User(
            id=user_id,
            email="test@example.com",
            name="Old Name"
        )

        # Mock the get_user_by_id call
        with patch.object(AuthService, 'get_user_by_id', return_value=mock_user):
            updates = {"name": "New Name", "image": "new-image.jpg"}

            result = await AuthService.update_user(db, user_id, updates)

            assert result == mock_user
            assert mock_user.name == "New Name"
            assert mock_user.image == "new-image.jpg"
            db.commit.assert_called_once()
            db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        """Test user update when user doesn't exist."""
        db = AsyncMock()
        user_id = uuid4()

        # Mock get_user_by_id to return None
        with patch.object(AuthService, 'get_user_by_id', return_value=None):
            result = await AuthService.update_user(db, user_id, {"name": "New Name"})

            assert result is None
            db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_account(self):
        """Test OAuth account creation."""
        db = AsyncMock()
        user_id = uuid4()

        account = await AuthService.create_account(
            db,
            user_id=user_id,
            provider="google",
            provider_account_id="google123",
            access_token="token123"
        )

        assert account.user_id == user_id
        assert account.provider == "google"
        assert account.provider_account_id == "google123"
        assert account.access_token == "token123"
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_account(self):
        """Test getting account by provider and provider account ID."""
        db = AsyncMock()

        mock_account = Account(
            id=uuid4(),
            provider="google",
            provider_account_id="google123"
        )

        # Create async mock for execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        db.execute.return_value = mock_result

        result = await AuthService.get_account(db, "google", "google123")

        assert result == mock_account
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_account(self):
        """Test updating OAuth account token data."""
        db = AsyncMock()
        account_id = uuid4()

        mock_account = Account(
            id=account_id,
            access_token="old_token"
        )

        # Create async mock for execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        db.execute.return_value = mock_result

        result = await AuthService.update_account(
            db, account_id, access_token="new_token", expires_at=1234567890
        )

        assert result == mock_account
        assert mock_account.access_token == "new_token"
        assert mock_account.expires_at == 1234567890
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test session creation."""
        db = AsyncMock()
        user_id = uuid4()
        session_token = "session123"
        expires = datetime.now(timezone.utc) + timedelta(days=7)

        session = await AuthService.create_session(
            db, user_id, session_token, expires
        )

        assert session.user_id == user_id
        assert session.session_token == session_token
        assert session.expires == expires
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_by_token(self):
        """Test getting session by token."""
        db = AsyncMock()
        session_token = "session123"

        mock_session = Session(
            id=uuid4(),
            session_token=session_token,
            user_id=uuid4()
        )

        # Create async mock for execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        db.execute.return_value = mock_result

        result = await AuthService.get_session_by_token(db, session_token)

        assert result == mock_session
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session(self):
        """Test session update."""
        db = AsyncMock()
        session_token = "session123"
        new_expires = datetime.now(timezone.utc) + timedelta(days=14)

        mock_session = Session(
            id=uuid4(),
            session_token=session_token,
            expires=datetime.now(timezone.utc) + timedelta(days=7)
        )

        # Create async mock for execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        db.execute.return_value = mock_result

        result = await AuthService.update_session(db, session_token, new_expires)

        assert result == mock_session
        assert mock_session.expires == new_expires
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session(self):
        """Test session deletion."""
        db = AsyncMock()
        session_token = "session123"

        # Create async mock for execute result with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 1
        db.execute.return_value = mock_result

        result = await AuthService.delete_session(db, session_token)

        assert result is True
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self):
        """Test session deletion when session doesn't exist."""
        db = AsyncMock()
        session_token = "nonexistent"

        # Create async mock for execute result with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 0
        db.execute.return_value = mock_result

        result = await AuthService.delete_session(db, session_token)

        assert result is False
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_verification_token(self):
        """Test verification token creation."""
        db = AsyncMock()
        identifier = "test@example.com"
        token = "verify123"
        expires = datetime.now(timezone.utc) + timedelta(hours=24)

        verification_token = await AuthService.create_verification_token(
            db, identifier, token, expires
        )

        assert verification_token.identifier == identifier
        assert verification_token.token == token
        assert verification_token.expires == expires
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_verification_token(self):
        """Test getting verification token."""
        db = AsyncMock()
        identifier = "test@example.com"
        token = "verify123"

        mock_token = VerificationToken(
            identifier=identifier,
            token=token,
            expires=datetime.now(timezone.utc) + timedelta(hours=24)
        )

        # Create async mock for execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        db.execute.return_value = mock_result

        result = await AuthService.get_verification_token(db, identifier, token)

        assert result == mock_token
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_verification_token(self):
        """Test verification token deletion."""
        db = AsyncMock()
        identifier = "test@example.com"
        token = "verify123"

        # Create async mock for execute result with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 1
        db.execute.return_value = mock_result

        result = await AuthService.delete_verification_token(db, identifier, token)

        assert result is True
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        db = AsyncMock()
        
        # Create async mock for execute result with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 5
        db.execute.return_value = mock_result

        result = await AuthService.cleanup_expired_sessions(db)

        assert result == 5
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_verification_tokens(self):
        """Test cleanup of expired verification tokens."""
        db = AsyncMock()
        
        # Create async mock for execute result with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 3
        db.execute.return_value = mock_result

        result = await AuthService.cleanup_expired_verification_tokens(db)

        assert result == 3
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_sessions(self):
        """Test getting user's active sessions."""
        db = AsyncMock()
        user_id = uuid4()

        mock_sessions = [
            Session(id=uuid4(), user_id=user_id, session_token="token1"),
            Session(id=uuid4(), user_id=user_id, session_token="token2")
        ]

        # Create async mock for execute result with scalars().all()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_sessions
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await AuthService.get_user_sessions(db, user_id)

        assert len(result) == 2
        assert result == mock_sessions
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_all_user_sessions(self):
        """Test revoking all sessions for a user."""
        db = AsyncMock()
        user_id = uuid4()

        # Create async mock for execute result with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 3
        db.execute.return_value = mock_result

        result = await AuthService.revoke_all_user_sessions(db, user_id)

        assert result == 3
        db.execute.assert_called_once()
        db.commit.assert_called_once()


class TestAuthServiceIntegration:
    """Integration tests with real database operations."""

    @pytest.mark.asyncio
    async def test_user_creation_and_retrieval_flow(self):
        """Test complete user creation and retrieval flow."""
        # This would require a real database setup for integration testing
        # For now, we'll test the service logic with mocked dependencies
        db = AsyncMock()

        # Test creating a user
        email = "integration@example.com"
        user = await AuthService.create_user(db, email=email, name="Integration User")

        # Verify the user was created with correct data
        assert user.email == email
        assert user.name == "Integration User"

        # Test account linking
        account = await AuthService.create_account(
            db,
            user_id=user.id,
            provider="google",
            provider_account_id="google456",
            access_token="access123"
        )

        assert account.user_id == user.id
        assert account.provider == "google"

    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        """Test complete session lifecycle."""
        db = AsyncMock()
        user_id = uuid4()
        session_token = "lifecycle_session"
        expires = datetime.now(timezone.utc) + timedelta(days=7)

        # Create session
        session = await AuthService.create_session(db, user_id, session_token, expires)
        assert session.session_token == session_token

        # Update session
        new_expires = datetime.now(timezone.utc) + timedelta(days=14)

        # Mock update behavior
        updated_session = Session(
            id=session.id,
            session_token=session_token,
            user_id=user_id,
            expires=new_expires
        )

        # Create async mock for execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = updated_session
        db.execute.return_value = mock_result

        result = await AuthService.update_session(db, session_token, new_expires)
        assert result.expires == new_expires

        # Delete session
        mock_delete_result = MagicMock()
        mock_delete_result.rowcount = 1
        db.execute.return_value = mock_delete_result
        
        deleted = await AuthService.delete_session(db, session_token)
        assert deleted is True


class TestAuthServiceErrorHandling:
    """Test error handling in AuthService."""

    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self):
        """Test updating a user that doesn't exist."""
        db = AsyncMock()

        with patch.object(AuthService, 'get_user_by_id', return_value=None):
            result = await AuthService.update_user(
                db, uuid4(), {"name": "New Name"}
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_update_nonexistent_account(self):
        """Test updating an account that doesn't exist."""
        db = AsyncMock()
        
        # Create async mock for execute result returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await AuthService.update_account(
            db, uuid4(), access_token="new_token"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_nonexistent_session(self):
        """Test updating a session that doesn't exist."""
        db = AsyncMock()
        
        # Create async mock for execute result returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await AuthService.update_session(
            db, "nonexistent", datetime.now(timezone.utc)
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_with_no_expired_data(self):
        """Test cleanup operations when no expired data exists."""
        db = AsyncMock()
        
        # Create async mock for execute result with rowcount 0
        mock_result = MagicMock()
        mock_result.rowcount = 0
        db.execute.return_value = mock_result

        # Test expired sessions cleanup
        sessions_cleaned = await AuthService.cleanup_expired_sessions(db)
        assert sessions_cleaned == 0

        # Test expired verification tokens cleanup
        tokens_cleaned = await AuthService.cleanup_expired_verification_tokens(db)
        assert tokens_cleaned == 0