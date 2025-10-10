"""
Tests for rate limiting and abuse prevention.

Tests cover:
- Generation rate limits (user-based and IP-based)
- Project quota enforcement
- Abuse detection patterns
- Error responses and retry-after headers
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import time

from app.middleware.rate_limit import GenerationRateLimiter
from app.services.quota_service import QuotaService
from app.services.abuse_service import AbuseDetectionService
from app.models.user import User
from app.models.project import Project


@pytest.fixture
async def rate_limiter():
    """Create rate limiter with in-memory store for testing."""
    limiter = GenerationRateLimiter(redis_url=None)  # Use in-memory
    await limiter.connect()
    yield limiter
    await limiter.close()


class TestGenerationRateLimiter:
    """Test Excel generation rate limiting."""

    @pytest.mark.asyncio
    async def test_free_tier_rate_limit_enforced(self, rate_limiter):
        """Test that free tier users are limited to 10 generations/hour."""
        user_id = str(uuid4())
        ip_address = "192.168.1.100"

        # Should allow first 10 requests
        for i in range(10):
            is_limited, retry_after = await rate_limiter.check_user_limit(
                user_id, "free"
            )
            assert not is_limited, f"Request {i+1} should not be limited"

        # 11th request should be limited
        is_limited, retry_after = await rate_limiter.check_user_limit(
            user_id, "free"
        )
        assert is_limited, "11th request should be rate limited"
        assert retry_after > 0, "Should provide retry-after time"

    @pytest.mark.asyncio
    async def test_pro_tier_unlimited(self, rate_limiter):
        """Test that pro tier users have unlimited generations."""
        user_id = str(uuid4())

        # Should allow many requests for pro tier
        for i in range(20):
            is_limited, retry_after = await rate_limiter.check_user_limit(
                user_id, "pro"
            )
            assert not is_limited, f"Pro tier request {i+1} should not be limited"

    @pytest.mark.asyncio
    async def test_enterprise_tier_unlimited(self, rate_limiter):
        """Test that enterprise tier users have unlimited generations."""
        user_id = str(uuid4())

        for i in range(20):
            is_limited, retry_after = await rate_limiter.check_user_limit(
                user_id, "enterprise"
            )
            assert not is_limited, f"Enterprise tier request {i+1} should not be limited"

    @pytest.mark.asyncio
    async def test_ip_rate_limit_enforced(self, rate_limiter):
        """Test that IP-based rate limiting prevents abuse."""
        ip_address = "192.168.1.200"

        # Should allow first 20 requests
        for i in range(20):
            is_limited, retry_after = await rate_limiter.check_ip_limit(ip_address)
            assert not is_limited, f"IP request {i+1} should not be limited"

        # 21st request should be limited
        is_limited, retry_after = await rate_limiter.check_ip_limit(ip_address)
        assert is_limited, "21st IP request should be rate limited"
        assert retry_after > 0, "Should provide retry-after time"

    @pytest.mark.asyncio
    async def test_different_users_separate_limits(self, rate_limiter):
        """Test that different users have separate rate limits."""
        user1 = str(uuid4())
        user2 = str(uuid4())

        # Max out user1's limit
        for i in range(10):
            await rate_limiter.check_user_limit(user1, "free")

        # User1 should be limited
        is_limited, _ = await rate_limiter.check_user_limit(user1, "free")
        assert is_limited, "User1 should be rate limited"

        # User2 should not be affected
        is_limited, _ = await rate_limiter.check_user_limit(user2, "free")
        assert not is_limited, "User2 should not be limited"


class TestQuotaService:
    """Test project quota enforcement."""

    @pytest.mark.asyncio
    async def test_free_tier_quota_enforced(self, db_session):
        """Test that free tier users are limited to 3 projects."""
        # Create user with free tier
        user = User(
            id=uuid4(),
            email="free@example.com",
            subscription_tier="free",
        )
        db_session.add(user)
        await db_session.commit()

        # Create 3 projects
        for i in range(3):
            project = Project(
                id=uuid4(),
                owner_id=user.id,
                name=f"Project {i+1}",
                description="Test project",
                configuration={},
            )
            db_session.add(project)
        await db_session.commit()

        quota_service = QuotaService(db_session)

        # Should not allow 4th project
        with pytest.raises(Exception) as exc_info:
            await quota_service.check_project_quota(user.id)

        assert exc_info.value.status_code == 403
        assert "quota_exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_pro_tier_unlimited_projects(self, db_session):
        """Test that pro tier users have unlimited projects."""
        user = User(
            id=uuid4(),
            email="pro@example.com",
            subscription_tier="pro",
        )
        db_session.add(user)
        await db_session.commit()

        # Create 10 projects
        for i in range(10):
            project = Project(
                id=uuid4(),
                owner_id=user.id,
                name=f"Project {i+1}",
                description="Test project",
                configuration={},
            )
            db_session.add(project)
        await db_session.commit()

        quota_service = QuotaService(db_session)

        # Should allow more projects
        await quota_service.check_project_quota(user.id)  # Should not raise

    @pytest.mark.asyncio
    async def test_quota_status_reporting(self, db_session):
        """Test quota status reporting provides accurate information."""
        user = User(
            id=uuid4(),
            email="user@example.com",
            subscription_tier="free",
        )
        db_session.add(user)
        await db_session.commit()

        # Create 2 projects
        for i in range(2):
            project = Project(
                id=uuid4(),
                owner_id=user.id,
                name=f"Project {i+1}",
                description="Test project",
                configuration={},
            )
            db_session.add(project)
        await db_session.commit()

        quota_service = QuotaService(db_session)
        status = await quota_service.get_quota_status(user.id)

        assert status["tier"] == "free"
        assert status["limit"] == 3
        assert status["used"] == 2
        assert status["remaining"] == 1
        assert status["percentage"] == pytest.approx(66.67, rel=0.1)


class TestAbuseDetectionService:
    """Test abuse detection and prevention."""

    @pytest.mark.asyncio
    async def test_rapid_creation_detection(self, db_session):
        """Test detection of rapid project creation."""
        user = User(
            id=uuid4(),
            email="suspicious@example.com",
            subscription_tier="free",
        )
        db_session.add(user)
        await db_session.commit()

        # Create 6 projects in quick succession
        now = datetime.utcnow()
        for i in range(6):
            project = Project(
                id=uuid4(),
                owner_id=user.id,
                name=f"Rapid Project {i+1}",
                description="Test project",
                configuration={},
                created_at=now - timedelta(minutes=i),
            )
            db_session.add(project)
        await db_session.commit()

        abuse_service = AbuseDetectionService(db_session)
        result = await abuse_service.check_rapid_project_creation(user.id)

        assert result["is_suspicious"] is True
        assert result["count"] >= 5

    @pytest.mark.asyncio
    async def test_unusual_count_detection(self, db_session):
        """Test detection of unusual project counts."""
        user = User(
            id=uuid4(),
            email="bulk@example.com",
            subscription_tier="free",
        )
        db_session.add(user)
        await db_session.commit()

        # Create 12 projects within an hour
        now = datetime.utcnow()
        for i in range(12):
            project = Project(
                id=uuid4(),
                owner_id=user.id,
                name=f"Bulk Project {i+1}",
                description="Test project",
                configuration={},
                created_at=now - timedelta(minutes=i * 5),
            )
            db_session.add(project)
        await db_session.commit()

        abuse_service = AbuseDetectionService(db_session)
        result = await abuse_service.check_unusual_project_count(user.id)

        assert result["is_suspicious"] is True
        assert result["count"] >= 10

    @pytest.mark.asyncio
    async def test_normal_usage_not_flagged(self, db_session):
        """Test that normal usage is not flagged as suspicious."""
        user = User(
            id=uuid4(),
            email="normal@example.com",
            subscription_tier="free",
        )
        db_session.add(user)
        await db_session.commit()

        # Create 3 projects spread over time
        now = datetime.utcnow()
        for i in range(3):
            project = Project(
                id=uuid4(),
                owner_id=user.id,
                name=f"Normal Project {i+1}",
                description="Test project",
                configuration={},
                created_at=now - timedelta(days=i),
            )
            db_session.add(project)
        await db_session.commit()

        abuse_service = AbuseDetectionService(db_session)
        result = await abuse_service.detect_suspicious_activity(user.id)

        assert result["is_suspicious"] is False

    @pytest.mark.asyncio
    async def test_should_throttle_user(self, db_session):
        """Test throttling decision based on abuse patterns."""
        user = User(
            id=uuid4(),
            email="abuser@example.com",
            subscription_tier="free",
        )
        db_session.add(user)
        await db_session.commit()

        # Create suspicious pattern
        now = datetime.utcnow()
        for i in range(11):
            project = Project(
                id=uuid4(),
                owner_id=user.id,
                name=f"Spam Project {i+1}",
                description="Test project",
                configuration={},
                created_at=now - timedelta(minutes=i),
            )
            db_session.add(project)
        await db_session.commit()

        abuse_service = AbuseDetectionService(db_session)
        should_throttle = await abuse_service.should_throttle_user(user.id)

        assert should_throttle is True


@pytest.fixture
async def db_session():
    """Create a test database session."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from app.database.connection import Base

    # Create test database engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()
