"""Tests for SessionService optimization and management."""

import pytest
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment variables before importing app modules
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['CORS_ORIGINS'] = '["http://localhost:3000"]'

from app.services.session_service import SessionService
from app.models.user import Session


class TestSessionService:
    """Test SessionService optimization and management operations."""

    @pytest.mark.asyncio
    async def test_optimize_session_storage(self):
        """Test session storage optimization."""
        db = AsyncMock()

        # Mock the cleanup and analysis methods
        with patch.object(SessionService, 'cleanup_expired_sessions', return_value=5) as mock_expired:
            with patch.object(SessionService, 'cleanup_duplicate_sessions', return_value=3) as mock_duplicates:
                with patch.object(SessionService, 'analyze_session_patterns', return_value={
                    "total_active_sessions": 10,
                    "average_session_duration_hours": 24.5
                }) as mock_patterns:

                    stats = await SessionService.optimize_session_storage(db)

                    assert stats["expired_sessions_cleaned"] == 5
                    assert stats["duplicate_sessions_cleaned"] == 3
                    assert stats["total_active_sessions"] == 10
                    assert stats["average_session_duration_hours"] == 24.5

                    mock_expired.assert_called_once_with(db)
                    mock_duplicates.assert_called_once_with(db)
                    mock_patterns.assert_called_once_with(db)

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        db = AsyncMock()

        # Create mock for execute result with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 7
        db.execute.return_value = mock_result

        result = await SessionService.cleanup_expired_sessions(db)

        assert result == 7
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_none_found(self):
        """Test cleanup when no expired sessions exist."""
        db = AsyncMock()

        # Create mock for execute result with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 0
        db.execute.return_value = mock_result

        result = await SessionService.cleanup_expired_sessions(db)

        assert result == 0
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_duplicate_sessions(self):
        """Test cleanup of duplicate sessions for users."""
        db = AsyncMock()

        # Mock finding users with multiple sessions
        user_id_1 = uuid4()
        user_id_2 = uuid4()

        # Mock delete operations
        session_id_1 = uuid4()
        session_id_2 = uuid4()
        delete_results = [MagicMock(rowcount=2), MagicMock(rowcount=1)]

        # Create scalars() mocks
        scalars_mock_1 = MagicMock()
        scalars_mock_1.all.return_value = [session_id_1]
        keep_sessions_1 = MagicMock()
        keep_sessions_1.scalars.return_value = scalars_mock_1

        scalars_mock_2 = MagicMock()
        scalars_mock_2.all.return_value = [session_id_2]
        keep_sessions_2 = MagicMock()
        keep_sessions_2.scalars.return_value = scalars_mock_2

        db.execute.side_effect = [
            MagicMock(all=lambda: [(user_id_1, 3), (user_id_2, 2)]),  # Users query
            keep_sessions_1,  # Keep sessions user 1 (uses scalars().all())
            delete_results[0],  # Delete user 1 duplicates
            keep_sessions_2,  # Keep sessions user 2 (uses scalars().all())
            delete_results[1],  # Delete user 2 duplicates
        ]

        result = await SessionService.cleanup_duplicate_sessions(db)

        assert result == 3  # 2 + 1 deleted sessions
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_session_patterns(self):
        """Test session pattern analysis."""
        db = AsyncMock()

        # Mock database query results
        mock_results = [
            MagicMock(scalar=lambda: 25),  # active_sessions
            MagicMock(scalar=lambda: 5),   # recent_sessions
            MagicMock(scalar=lambda: 15),  # daily_sessions
            MagicMock(scalar=lambda: 22),  # weekly_sessions
            MagicMock(scalar=lambda: 12.5), # avg_duration
            MagicMock(scalar=lambda: 18)   # unique_users
        ]

        db.execute.side_effect = mock_results

        result = await SessionService.analyze_session_patterns(db)

        assert result["total_active_sessions"] == 25
        assert result["sessions_last_hour"] == 5
        assert result["sessions_last_day"] == 15
        assert result["sessions_last_week"] == 22
        assert result["average_session_duration_hours"] == 12.5
        assert result["unique_active_users"] == 18

    @pytest.mark.asyncio
    async def test_get_session_health_metrics(self):
        """Test getting session health metrics."""
        db = AsyncMock()

        # Mock database query results
        mock_results = [
            MagicMock(scalar=lambda: 100),  # total_sessions
            MagicMock(scalar=lambda: 75),   # active_sessions
            MagicMock(scalar=lambda: 25),   # expired_sessions
            MagicMock(scalar=lambda: 10),   # sessions_24h
            MagicMock(scalar=lambda: 30),   # sessions_7d
            MagicMock(scalar=lambda: 85),   # sessions_30d
            MagicMock(scalar=lambda: 5)     # expiring_soon
        ]

        db.execute.side_effect = mock_results

        result = await SessionService.get_session_health_metrics(db)

        assert result["total_sessions"] == 100
        assert result["active_sessions"] == 75
        assert result["expired_sessions"] == 25
        assert result["sessions_created_24h"] == 10
        assert result["sessions_created_7d"] == 30
        assert result["sessions_created_30d"] == 85
        assert result["sessions_expiring_within_1h"] == 5
        assert result["health_ratio"] == 75.0  # 75/100 * 100

    @pytest.mark.asyncio
    async def test_extend_session(self):
        """Test extending session expiration."""
        db = AsyncMock()
        session_token = "extend_session_token"
        session_id = uuid4()

        # Create mock session that's not expired
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_session = Session(
            id=session_id,
            session_token=session_token,
            expires=future_time
        )

        # Create mock for execute result


        mock_result = MagicMock()


        mock_result.scalar_one_or_none.return_value = mock_session


        db.execute.return_value = mock_result

        result = await SessionService.extend_session(db, session_token, hours=48)

        assert result == mock_session
        # Check that expires was updated (should be ~48 hours from now)
        expected_expiry = datetime.now(timezone.utc) + timedelta(hours=48)
        time_diff = abs((mock_session.expires - expected_expiry).total_seconds())
        assert time_diff < 10  # Allow 10 second tolerance

        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_extend_session_not_found(self):
        """Test extending non-existent session."""
        db = AsyncMock()
        # Create mock for execute result

        mock_result = MagicMock()

        mock_result.scalar_one_or_none.return_value = None

        db.execute.return_value = mock_result

        result = await SessionService.extend_session(db, "nonexistent", hours=24)

        assert result is None
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_extend_expired_session(self):
        """Test extending already expired session."""
        db = AsyncMock()
        session_token = "expired_session"

        # Create mock expired session
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_session = Session(
            id=uuid4(),
            session_token=session_token,
            expires=past_time
        )

        # Create mock for execute result


        mock_result = MagicMock()


        mock_result.scalar_one_or_none.return_value = mock_session


        db.execute.return_value = mock_result

        result = await SessionService.extend_session(db, session_token, hours=24)

        assert result is None  # Cannot extend expired session
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_cleanup_sessions(self):
        """Test batch cleanup of expired sessions."""
        db = AsyncMock()

        # Mock three batches: full batch, partial batch, empty batch
        batch1_ids = [uuid4() for _ in range(1000)]  # Full batch
        batch2_ids = [uuid4() for _ in range(500)]   # Partial batch
        batch3_ids = []  # Empty batch (end)

        mock_query_results = [
            MagicMock(all=lambda: [[sid] for sid in batch1_ids]),
            MagicMock(all=lambda: [[sid] for sid in batch2_ids]),
            MagicMock(all=lambda: batch3_ids)
        ]

        mock_delete_results = [
            MagicMock(rowcount=1000),  # First batch deleted
            MagicMock(rowcount=500)    # Second batch deleted
        ]

        # Set up side effects
        db.execute.side_effect = [
            mock_query_results[0],  # First query
            mock_delete_results[0], # First delete
            mock_query_results[1],  # Second query
            mock_delete_results[1], # Second delete
            mock_query_results[2]   # Third query (empty)
        ]

        result = await SessionService.batch_cleanup_sessions(db, batch_size=1000)

        assert result == 1500  # 1000 + 500
        assert db.commit.call_count == 2  # Once per batch

    @pytest.mark.asyncio
    async def test_batch_cleanup_sessions_no_expired(self):
        """Test batch cleanup when no expired sessions exist."""
        db = AsyncMock()

        # Mock empty result
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result = await SessionService.batch_cleanup_sessions(db)

        assert result == 0
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_session_history(self):
        """Test getting user session history."""
        db = AsyncMock()
        user_id = uuid4()

        now = datetime.now(timezone.utc)
        sessions = [
            Session(
                id=uuid4(),
                user_id=user_id,
                created_at=now - timedelta(hours=1),
                expires=now + timedelta(hours=23)  # Active session
            ),
            Session(
                id=uuid4(),
                user_id=user_id,
                created_at=now - timedelta(hours=25),
                expires=now - timedelta(hours=1)   # Expired session
            )
        ]

        # Create mock for execute result with scalars().all()


        mock_scalars = MagicMock()


        mock_scalars.all.return_value = sessions


        mock_result = MagicMock()


        mock_result.scalars.return_value = mock_scalars


        db.execute.return_value = mock_result

        result = await SessionService.get_user_session_history(db, user_id, limit=10)

        assert len(result) == 2

        # Check active session
        active_session = result[0]
        assert active_session["is_active"] is True
        assert active_session["duration_hours"] == 24.0
        assert active_session["time_remaining_hours"] > 0

        # Check expired session
        expired_session = result[1]
        assert expired_session["is_active"] is False
        assert expired_session["time_remaining_hours"] == 0

    @pytest.mark.asyncio
    async def test_get_user_session_history_empty(self):
        """Test getting session history when user has no sessions."""
        db = AsyncMock()
        # Create mock for execute result with scalars().all()

        mock_scalars = MagicMock()

        mock_scalars.all.return_value = []

        mock_result = MagicMock()

        mock_result.scalars.return_value = mock_scalars

        db.execute.return_value = mock_result

        result = await SessionService.get_user_session_history(db, uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_health_ratio_calculation_with_zero_total(self):
        """Test health ratio calculation when total sessions is zero."""
        db = AsyncMock()

        # Mock database query results with zero total sessions
        mock_results = [
            MagicMock(scalar=lambda: 0),   # total_sessions
            MagicMock(scalar=lambda: 0),   # active_sessions
            MagicMock(scalar=lambda: 0),   # expired_sessions
            MagicMock(scalar=lambda: 0),   # sessions_24h
            MagicMock(scalar=lambda: 0),   # sessions_7d
            MagicMock(scalar=lambda: 0),   # sessions_30d
            MagicMock(scalar=lambda: 0)    # expiring_soon
        ]

        db.execute.side_effect = mock_results

        result = await SessionService.get_session_health_metrics(db)

        assert result["health_ratio"] == 0.0  # Should not divide by zero


class TestSessionServiceIntegration:
    """Integration tests for SessionService."""

    @pytest.mark.asyncio
    async def test_full_optimization_cycle(self):
        """Test complete optimization cycle."""
        db = AsyncMock()

        # Mock all the operations
        with patch.object(SessionService, 'cleanup_expired_sessions', return_value=10):
            with patch.object(SessionService, 'cleanup_duplicate_sessions', return_value=5):
                with patch.object(SessionService, 'analyze_session_patterns', return_value={
                    "total_active_sessions": 50,
                    "sessions_last_hour": 5,
                    "average_session_duration_hours": 18.5,
                    "unique_active_users": 35
                }):

                    stats = await SessionService.optimize_session_storage(db)

                    # Verify all operations completed
                    assert stats["expired_sessions_cleaned"] == 10
                    assert stats["duplicate_sessions_cleaned"] == 5
                    assert stats["total_active_sessions"] == 50
                    assert stats["sessions_last_hour"] == 5
                    assert stats["average_session_duration_hours"] == 18.5
                    assert stats["unique_active_users"] == 35

    @pytest.mark.asyncio
    async def test_session_lifecycle_management(self):
        """Test managing session through its lifecycle."""
        db = AsyncMock()
        session_token = "lifecycle_test"
        user_id = uuid4()

        # Step 1: Session exists and is active
        active_session = Session(
            id=uuid4(),
            session_token=session_token,
            user_id=user_id,
            expires=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        # Test extending the session
        # Create mock for execute result

        mock_result = MagicMock()

        mock_result.scalar_one_or_none.return_value = active_session

        db.execute.return_value = mock_result
        extended = await SessionService.extend_session(db, session_token, hours=24)

        assert extended == active_session
        # Session should now expire ~24 hours from now
        expected_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        time_diff = abs((active_session.expires - expected_expiry).total_seconds())
        assert time_diff < 10  # Allow small time difference

        # Step 2: Later, session gets cleaned up in optimization
        with patch.object(SessionService, 'batch_cleanup_sessions', return_value=1) as mock_cleanup:
            cleaned = await SessionService.batch_cleanup_sessions(db)
            assert cleaned == 1
            mock_cleanup.assert_called_once()


class TestSessionServiceErrorHandling:
    """Test error handling in SessionService."""

    @pytest.mark.asyncio
    async def test_analyze_patterns_with_null_average(self):
        """Test session pattern analysis when average duration is null."""
        db = AsyncMock()

        # Mock database query results with null average
        mock_results = [
            MagicMock(scalar=lambda: 25),  # active_sessions
            MagicMock(scalar=lambda: 5),   # recent_sessions
            MagicMock(scalar=lambda: 15),  # daily_sessions
            MagicMock(scalar=lambda: 22),  # weekly_sessions
            MagicMock(scalar=lambda: None), # avg_duration (null)
            MagicMock(scalar=lambda: 18)   # unique_users
        ]

        db.execute.side_effect = mock_results

        result = await SessionService.analyze_session_patterns(db)

        assert result["average_session_duration_hours"] == 0  # Should default to 0
        assert result["total_active_sessions"] == 25

    @pytest.mark.asyncio
    async def test_cleanup_duplicate_sessions_no_duplicates(self):
        """Test cleanup when no users have duplicate sessions."""
        db = AsyncMock()

        # Mock empty result for users with multiple sessions
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        result = await SessionService.cleanup_duplicate_sessions(db)

        assert result == 0
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_extend_session_with_invalid_hours(self):
        """Test extending session with edge case hours."""
        db = AsyncMock()
        session_token = "test_session"

        # Create mock session
        mock_session = Session(
            id=uuid4(),
            session_token=session_token,
            expires=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        # Create mock for execute result


        mock_result = MagicMock()


        mock_result.scalar_one_or_none.return_value = mock_session


        db.execute.return_value = mock_result

        # Test with 0 hours (should work but not extend much)
        result = await SessionService.extend_session(db, session_token, hours=0)

        assert result == mock_session
        # Should be extended to now + 0 hours (essentially now)
        time_diff = abs((mock_session.expires - datetime.now(timezone.utc)).total_seconds())
        assert time_diff < 10  # Should be very close to now