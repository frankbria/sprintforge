"""Tests for database integration functionality - Task 2.4."""

import pytest
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

# Set environment variables before importing app modules
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['CORS_ORIGINS'] = '["http://localhost:3000"]'


class TestDatabaseIntegration:
    """Test database integration features for Task 2.4."""

    @pytest.mark.asyncio
    async def test_auth_service_import_and_methods(self):
        """Test that AuthService can be imported and has required methods."""
        from app.services.auth_service import AuthService

        # Verify all required methods exist
        required_methods = [
            'create_user', 'get_user_by_id', 'get_user_by_email', 'update_user',
            'create_account', 'get_account', 'update_account',
            'create_session', 'get_session_by_token', 'update_session', 'delete_session',
            'create_verification_token', 'get_verification_token', 'delete_verification_token',
            'cleanup_expired_sessions', 'cleanup_expired_verification_tokens',
            'get_user_sessions', 'revoke_all_user_sessions'
        ]

        for method_name in required_methods:
            assert hasattr(AuthService, method_name), f"Missing method: {method_name}"
            method = getattr(AuthService, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    @pytest.mark.asyncio
    async def test_user_service_import_and_methods(self):
        """Test that UserService can be imported and has required methods."""
        from app.services.user_service import UserService

        # Verify all required methods exist
        required_methods = [
            'sync_user_from_oauth', 'update_user_profile', 'update_user_preferences',
            'get_user_with_accounts', 'get_user_statistics', 'deactivate_user',
            'reactivate_user', 'search_users', 'get_recent_users'
        ]

        for method_name in required_methods:
            assert hasattr(UserService, method_name), f"Missing method: {method_name}"
            method = getattr(UserService, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    @pytest.mark.asyncio
    async def test_session_service_import_and_methods(self):
        """Test that SessionService can be imported and has required methods."""
        from app.services.session_service import SessionService

        # Verify all required methods exist
        required_methods = [
            'optimize_session_storage', 'cleanup_expired_sessions', 'cleanup_duplicate_sessions',
            'analyze_session_patterns', 'get_session_health_metrics', 'extend_session',
            'batch_cleanup_sessions', 'get_user_session_history'
        ]

        for method_name in required_methods:
            assert hasattr(SessionService, method_name), f"Missing method: {method_name}"
            method = getattr(SessionService, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    @pytest.mark.asyncio
    async def test_database_models_import(self):
        """Test that database models can be imported."""
        from app.models.user import User, Account, Session, VerificationToken

        # Verify model classes exist
        assert User is not None
        assert Account is not None
        assert Session is not None
        assert VerificationToken is not None

        # Verify models have required tablenames
        assert User.__tablename__ == "users"
        assert Account.__tablename__ == "accounts"
        assert Session.__tablename__ == "sessions"
        assert VerificationToken.__tablename__ == "verification_tokens"

    @pytest.mark.asyncio
    async def test_services_package_exports(self):
        """Test that services package exports all services."""
        from app.services import AuthService, UserService, SessionService

        assert AuthService is not None
        assert UserService is not None
        assert SessionService is not None

    @pytest.mark.asyncio
    async def test_user_creation_workflow(self):
        """Test user creation workflow with mocked database."""
        from app.services.auth_service import AuthService

        # Mock database session
        db = AsyncMock()

        # Test user creation
        email = "workflow@example.com"
        name = "Workflow User"

        # Mock the User object creation
        with patch('app.services.auth_service.User') as MockUser:
            mock_user_instance = MagicMock()
            mock_user_instance.id = uuid4()
            mock_user_instance.email = email
            mock_user_instance.name = name
            MockUser.return_value = mock_user_instance

            user = await AuthService.create_user(db, email=email, name=name)

            # Verify user creation process
            MockUser.assert_called_once()
            call_kwargs = MockUser.call_args[1]
            assert call_kwargs['email'] == email
            assert call_kwargs['name'] == name
            db.add.assert_called_once_with(mock_user_instance)
            db.commit.assert_awaited_once()
            db.refresh.assert_awaited_once_with(mock_user_instance)

    @pytest.mark.asyncio
    async def test_oauth_synchronization_workflow(self):
        """Test OAuth user synchronization workflow."""
        from app.services.user_service import UserService

        db = AsyncMock()

        # Mock no existing account - db.execute() returns a coroutine that needs to be awaited
        execute_result_1 = MagicMock()
        execute_result_1.scalar_one_or_none.return_value = None
        execute_result_2 = MagicMock()
        execute_result_2.scalar_one_or_none.return_value = None
        db.execute.return_value = execute_result_1
        db.execute.side_effect = [execute_result_1, execute_result_2]

        oauth_profile = {
            "email": "oauth@example.com",
            "name": "OAuth User",
            "image": "https://example.com/avatar.jpg",
            "email_verified": True
        }

        # Mock user creation method
        with patch.object(UserService, '_create_user_from_oauth_profile', new_callable=AsyncMock) as mock_create:
            mock_user = MagicMock()
            mock_user.email = oauth_profile["email"]
            mock_user.name = oauth_profile["name"]
            mock_create.return_value = mock_user

            result = await UserService.sync_user_from_oauth(
                db, "google", "google123", oauth_profile
            )

            # Verify OAuth sync process
            assert result == mock_user
            mock_create.assert_awaited_once_with(db, oauth_profile)

    @pytest.mark.asyncio
    async def test_session_optimization_workflow(self):
        """Test session optimization workflow."""
        from app.services.session_service import SessionService

        db = AsyncMock()

        # Mock cleanup operations
        with patch.object(SessionService, 'cleanup_expired_sessions', return_value=5) as mock_expired:
            with patch.object(SessionService, 'cleanup_duplicate_sessions', return_value=3) as mock_duplicates:
                with patch.object(SessionService, 'analyze_session_patterns', return_value={
                    "total_active_sessions": 50,
                    "average_session_duration_hours": 24.0
                }) as mock_patterns:

                    stats = await SessionService.optimize_session_storage(db)

                    # Verify optimization workflow
                    assert stats["expired_sessions_cleaned"] == 5
                    assert stats["duplicate_sessions_cleaned"] == 3
                    assert stats["total_active_sessions"] == 50
                    assert stats["average_session_duration_hours"] == 24.0

                    mock_expired.assert_called_once_with(db)
                    mock_duplicates.assert_called_once_with(db)
                    mock_patterns.assert_called_once_with(db)

    @pytest.mark.asyncio
    async def test_account_linking_workflow(self):
        """Test OAuth account linking workflow."""
        from app.services.auth_service import AuthService

        db = AsyncMock()
        user_id = uuid4()

        # Mock account creation
        with patch('app.services.auth_service.Account') as MockAccount:
            mock_account_instance = MagicMock()
            mock_account_instance.id = uuid4()
            mock_account_instance.user_id = user_id
            mock_account_instance.provider = "microsoft"
            mock_account_instance.provider_account_id = "ms456"
            MockAccount.return_value = mock_account_instance

            account = await AuthService.create_account(
                db,
                user_id=user_id,
                provider="microsoft",
                provider_account_id="ms456",
                access_token="token123"
            )

            # Verify account linking process
            MockAccount.assert_called_once()
            db.add.assert_called_once_with(mock_account_instance)
            db.commit.assert_called_once()
            db.refresh.assert_called_once_with(mock_account_instance)

    @pytest.mark.asyncio
    async def test_session_management_workflow(self):
        """Test session management workflow."""
        from app.services.auth_service import AuthService

        db = AsyncMock()
        user_id = uuid4()
        session_token = "test_session_token"
        expires = datetime.now(timezone.utc) + timedelta(days=7)

        # Mock session creation
        with patch('app.services.auth_service.Session') as MockSession:
            mock_session_instance = MagicMock()
            mock_session_instance.id = uuid4()
            mock_session_instance.user_id = user_id
            mock_session_instance.session_token = session_token
            mock_session_instance.expires = expires
            MockSession.return_value = mock_session_instance

            session = await AuthService.create_session(db, user_id, session_token, expires)

            # Verify session creation process
            MockSession.assert_called_once_with(
                user_id=user_id,
                session_token=session_token,
                expires=expires
            )
            db.add.assert_called_once_with(mock_session_instance)
            db.commit.assert_called_once()
            db.refresh.assert_called_once_with(mock_session_instance)

    @pytest.mark.asyncio
    async def test_verification_token_workflow(self):
        """Test verification token workflow."""
        from app.services.auth_service import AuthService

        db = AsyncMock()
        identifier = "verify@example.com"
        token = "verification_token_123"
        expires = datetime.now(timezone.utc) + timedelta(hours=24)

        # Mock verification token creation
        with patch('app.services.auth_service.VerificationToken') as MockToken:
            mock_token_instance = MagicMock()
            mock_token_instance.identifier = identifier
            mock_token_instance.token = token
            mock_token_instance.expires = expires
            MockToken.return_value = mock_token_instance

            verification_token = await AuthService.create_verification_token(
                db, identifier, token, expires
            )

            # Verify verification token creation process
            MockToken.assert_called_once_with(
                identifier=identifier,
                token=token,
                expires=expires
            )
            db.add.assert_called_once_with(mock_token_instance)
            db.commit.assert_called_once()
            db.refresh.assert_called_once_with(mock_token_instance)

    @pytest.mark.asyncio
    async def test_user_preferences_workflow(self):
        """Test user preferences management workflow."""
        from app.services.user_service import UserService

        db = AsyncMock()
        user_id = uuid4()

        # Mock user with existing preferences
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.preferences = {"theme": "dark", "notifications": True}
        mock_user.updated_at = datetime.now(timezone.utc)

        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = mock_user
        db.execute.return_value = execute_result

        new_preferences = {"theme": "light", "language": "es"}

        result = await UserService.update_user_preferences(db, user_id, new_preferences)

        # Verify preferences update workflow
        assert result == mock_user
        expected_prefs = {
            "theme": "light",      # Updated
            "notifications": True, # Preserved
            "language": "es"       # Added
        }
        assert mock_user.preferences == expected_prefs
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_session_extension_workflow(self):
        """Test session extension workflow."""
        from app.services.session_service import SessionService

        db = AsyncMock()
        session_token = "extend_me"

        # Mock active session
        mock_session = MagicMock()
        mock_session.id = uuid4()
        mock_session.session_token = session_token
        mock_session.expires = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_session.updated_at = datetime.now(timezone.utc)

        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = mock_session
        db.execute.return_value = execute_result

        result = await SessionService.extend_session(db, session_token, hours=48)

        # Verify session extension workflow
        assert result == mock_session
        # Session should be extended by approximately 48 hours
        expected_expiry = datetime.now(timezone.utc) + timedelta(hours=48)
        time_diff = abs((mock_session.expires - expected_expiry).total_seconds())
        assert time_diff < 10  # Allow 10 second tolerance

        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_cleanup_operations_workflow(self):
        """Test cleanup operations workflow."""
        from app.services.auth_service import AuthService

        db = AsyncMock()

        # Mock cleanup results
        db.execute.return_value.rowcount = 12

        # Test expired sessions cleanup
        cleaned_sessions = await AuthService.cleanup_expired_sessions(db)
        assert cleaned_sessions == 12

        # Test expired verification tokens cleanup
        cleaned_tokens = await AuthService.cleanup_expired_verification_tokens(db)
        assert cleaned_tokens == 12

        # Verify cleanup workflow
        assert db.execute.call_count == 2
        assert db.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_user_statistics_workflow(self):
        """Test user statistics generation workflow."""
        from app.services.user_service import UserService

        db = AsyncMock()
        user_id = uuid4()

        # Mock user with accounts
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "stats@example.com"
        mock_user.name = "Stats User"
        mock_user.created_at = datetime.now(timezone.utc)
        mock_user.updated_at = datetime.now(timezone.utc)
        mock_user.subscription_tier = "pro"
        mock_user.subscription_status = "active"
        mock_user.email_verified = datetime.now(timezone.utc)
        mock_user.image = "https://example.com/avatar.jpg"
        mock_user.preferences = {"theme": "dark", "notifications": True}

        # Mock accounts
        mock_account1 = MagicMock()
        mock_account1.provider = "google"
        mock_account2 = MagicMock()
        mock_account2.provider = "microsoft"
        mock_user.accounts = [mock_account1, mock_account2]

        # Mock service methods
        with patch.object(UserService, 'get_user_with_accounts', new_callable=AsyncMock, return_value=mock_user):
            with patch('app.services.auth_service.AuthService.get_user_sessions', new_callable=AsyncMock) as mock_sessions:
                mock_sessions.return_value = ["session1", "session2", "session3"]

                stats = await UserService.get_user_statistics(db, user_id)

                # Verify statistics workflow
                assert stats["user_id"] == str(user_id)
                assert stats["email"] == "stats@example.com"
                assert stats["subscription_tier"] == "pro"
                assert stats["linked_accounts"] == 2
                assert stats["oauth_providers"] == ["google", "microsoft"]
                assert stats["active_sessions"] == 3
                assert stats["email_verified"] is True
                assert stats["has_profile_image"] is True
                assert stats["preferences_set"] == 2


class TestDatabaseIntegrationErrorHandling:
    """Test error handling in database integration."""

    @pytest.mark.asyncio
    async def test_missing_oauth_email_error(self):
        """Test error handling when OAuth profile lacks email."""
        from app.services.user_service import UserService

        db = AsyncMock()

        # Mock no existing account
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        db.execute.return_value = execute_result

        oauth_profile = {"name": "No Email User"}

        with pytest.raises(ValueError, match="OAuth profile missing email address"):
            await UserService.sync_user_from_oauth(
                db, "google", "google123", oauth_profile
            )

    @pytest.mark.asyncio
    async def test_extend_expired_session_error(self):
        """Test error handling when extending expired session."""
        from app.services.session_service import SessionService

        db = AsyncMock()
        session_token = "expired_session"

        # Mock expired session
        mock_session = MagicMock()
        mock_session.id = uuid4()
        mock_session.expires = datetime.now(timezone.utc) - timedelta(hours=1)

        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = mock_session
        db.execute.return_value = execute_result

        result = await SessionService.extend_session(db, session_token, hours=24)

        # Should return None for expired session
        assert result is None
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_nonexistent_user_error(self):
        """Test error handling when updating non-existent user."""
        from app.services.auth_service import AuthService

        db = AsyncMock()

        # Mock get_user_by_id to return None
        with patch.object(AuthService, 'get_user_by_id', return_value=None):
            result = await AuthService.update_user(
                db, uuid4(), {"name": "New Name"}
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self):
        """Test deleting non-existent session."""
        from app.services.auth_service import AuthService

        db = AsyncMock()
        db.execute.return_value.rowcount = 0

        result = await AuthService.delete_session(db, "nonexistent_session")

        assert result is False
        db.execute.assert_called_once()
        db.commit.assert_called_once()


class TestDatabaseIntegrationPerformance:
    """Test performance considerations in database integration."""

    @pytest.mark.asyncio
    async def test_batch_cleanup_performance(self):
        """Test batch cleanup for performance."""
        from app.services.session_service import SessionService

        db = AsyncMock()

        # Mock batch cleanup scenario
        batch_size = 1000

        # First batch: full
        batch1_ids = [uuid4() for _ in range(batch_size)]
        # Second batch: partial
        batch2_ids = [uuid4() for _ in range(500)]
        # Third batch: empty (end)
        batch3_ids = []

        # Mock query results
        db.execute.side_effect = [
            # Queries for expired session IDs
            MagicMock(all=lambda: [[sid] for sid in batch1_ids]),
            # Delete operations
            MagicMock(rowcount=batch_size),
            # Second query
            MagicMock(all=lambda: [[sid] for sid in batch2_ids]),
            # Second delete
            MagicMock(rowcount=500),
            # Third query (empty)
            MagicMock(all=lambda: batch3_ids)
        ]

        result = await SessionService.batch_cleanup_sessions(db, batch_size=batch_size)

        # Verify batch processing
        assert result == 1500  # 1000 + 500
        assert db.commit.call_count == 2  # Once per non-empty batch

    @pytest.mark.asyncio
    async def test_session_health_metrics_calculation(self):
        """Test session health metrics calculation."""
        from app.services.session_service import SessionService

        db = AsyncMock()

        # Mock health metrics
        mock_results = [
            MagicMock(scalar=lambda: 100),  # total_sessions
            MagicMock(scalar=lambda: 85),   # active_sessions
            MagicMock(scalar=lambda: 15),   # expired_sessions
            MagicMock(scalar=lambda: 20),   # sessions_24h
            MagicMock(scalar=lambda: 45),   # sessions_7d
            MagicMock(scalar=lambda: 90),   # sessions_30d
            MagicMock(scalar=lambda: 10)    # expiring_soon
        ]

        db.execute.side_effect = mock_results

        health = await SessionService.get_session_health_metrics(db)

        # Verify health calculations
        assert health["total_sessions"] == 100
        assert health["active_sessions"] == 85
        assert health["health_ratio"] == 85.0  # 85/100 * 100
        assert health["sessions_expiring_within_1h"] == 10

    @pytest.mark.asyncio
    async def test_duplicate_session_cleanup_efficiency(self):
        """Test efficient duplicate session cleanup."""
        from app.services.session_service import SessionService

        db = AsyncMock()

        # Mock users with multiple sessions
        user1_id = uuid4()
        user2_id = uuid4()

        # Mock finding users with duplicates
        db.execute.return_value.all.side_effect = [
            [(user1_id, 4), (user2_id, 3)],  # Users with multiple sessions
            [uuid4()],  # Sessions to keep for user1
            [uuid4()]   # Sessions to keep for user2
        ]

        # Mock delete operations
        delete_mock1 = MagicMock(rowcount=3)  # Deleted 3 duplicates for user1
        delete_mock2 = MagicMock(rowcount=2)  # Deleted 2 duplicates for user2

        # Create proper mock objects for each query
        mock_users_result = MagicMock()
        mock_users_result.all.return_value = [(user1_id, 4), (user2_id, 3)]

        mock_keep1_result = MagicMock()
        keep1_id = uuid4()
        mock_keep1_scalars = MagicMock()
        mock_keep1_scalars.all.return_value = [keep1_id]
        mock_keep1_result.scalars.return_value = mock_keep1_scalars

        mock_keep2_result = MagicMock()
        keep2_id = uuid4()
        mock_keep2_scalars = MagicMock()
        mock_keep2_scalars.all.return_value = [keep2_id]
        mock_keep2_result.scalars.return_value = mock_keep2_scalars

        db.execute.side_effect = [
            # Initial query for users with multiple sessions
            mock_users_result,
            # Query sessions to keep for user1
            mock_keep1_result,
            # Delete duplicates for user1
            delete_mock1,
            # Query sessions to keep for user2
            mock_keep2_result,
            # Delete duplicates for user2
            delete_mock2
        ]

        result = await SessionService.cleanup_duplicate_sessions(db)

        # Verify efficient cleanup
        assert result == 5  # 3 + 2 deleted duplicates
        db.commit.assert_called_once()  # Single commit at the end