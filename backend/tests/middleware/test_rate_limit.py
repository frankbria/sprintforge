"""
Unit tests for rate limiting middleware.

Tests cover:
- Free tier rate limits (10/hour)
- Pro/Enterprise unlimited access
- IP-based limits (20/hour)
- Different users get separate limits
"""

import pytest
from uuid import uuid4

from app.middleware.rate_limit import GenerationRateLimiter


class TestGenerationRateLimiter:
    """Test Excel generation rate limiting."""

    @pytest.mark.asyncio
    async def test_free_tier_rate_limit_enforced(self):
        """Test that free tier users are limited to 10 generations/hour."""
        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user_id = str(uuid4())

        # Should allow first 10 requests
        for i in range(10):
            is_limited, retry_after = await limiter.check_user_limit(user_id, "free")
            assert not is_limited, f"Request {i+1} should not be limited"

        # 11th request should be limited
        is_limited, retry_after = await limiter.check_user_limit(user_id, "free")
        assert is_limited, "11th request should be rate limited"
        assert retry_after > 0, "Should provide retry-after time"

        await limiter.close()

    @pytest.mark.asyncio
    async def test_pro_tier_unlimited(self):
        """Test that pro tier users have unlimited generations."""
        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user_id = str(uuid4())

        # Should allow many requests for pro tier
        for i in range(20):
            is_limited, retry_after = await limiter.check_user_limit(user_id, "pro")
            assert not is_limited, f"Pro tier request {i+1} should not be limited"

        await limiter.close()

    @pytest.mark.asyncio
    async def test_enterprise_tier_unlimited(self):
        """Test that enterprise tier users have unlimited generations."""
        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user_id = str(uuid4())

        for i in range(20):
            is_limited, retry_after = await limiter.check_user_limit(user_id, "enterprise")
            assert not is_limited, f"Enterprise tier request {i+1} should not be limited"

        await limiter.close()

    @pytest.mark.asyncio
    async def test_ip_rate_limit_enforced(self):
        """Test that IP-based rate limiting prevents abuse."""
        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        # Use completely unique IP each time
        ip_address = f"10.{uuid4().int % 255}.{uuid4().int % 255}.{uuid4().int % 255}"

        # Clear any existing data for this IP
        if limiter.redis_client:
            key = limiter._get_redis_key(ip_address, "ip")
            await limiter.redis_client.delete(key)

        # Should allow first 20 requests
        for i in range(20):
            is_limited, retry_after = await limiter.check_ip_limit(ip_address)
            if is_limited:
                print(f"Request {i+1} was limited unexpectedly")
            assert not is_limited, f"IP request {i+1} should not be limited"

        # 21st request should be limited
        is_limited, retry_after = await limiter.check_ip_limit(ip_address)
        assert is_limited, "21st IP request should be rate limited"
        assert retry_after > 0, "Should provide retry-after time"

        await limiter.close()

    @pytest.mark.asyncio
    async def test_different_users_separate_limits(self):
        """Test that different users have separate rate limits."""
        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user1 = str(uuid4())
        user2 = str(uuid4())

        # Max out user1's limit
        for i in range(10):
            await limiter.check_user_limit(user1, "free")

        # User1 should be limited
        is_limited, _ = await limiter.check_user_limit(user1, "free")
        assert is_limited, "User1 should be rate limited"

        # User2 should not be affected
        is_limited, _ = await limiter.check_user_limit(user2, "free")
        assert not is_limited, "User2 should not be limited"

        await limiter.close()

    @pytest.mark.asyncio
    async def test_check_generation_limit_success(self):
        """Test successful generation limit check."""
        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user_id = str(uuid4())
        ip_address = "192.168.1.1"

        # Should not raise exception for free tier within limits
        await limiter.check_generation_limit(user_id, ip_address, "free")

        await limiter.close()

    @pytest.mark.asyncio
    async def test_check_generation_limit_user_exceeded(self):
        """Test that HTTPException is raised when user limit exceeded."""
        from fastapi import HTTPException

        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user_id = str(uuid4())
        ip_address = "192.168.1.2"

        # Max out user limit
        for i in range(10):
            await limiter.check_user_limit(user_id, "free")

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_generation_limit(user_id, ip_address, "free")

        assert exc_info.value.status_code == 429
        assert "rate_limit_exceeded" in str(exc_info.value.detail)

        await limiter.close()

    @pytest.mark.asyncio
    async def test_check_generation_limit_ip_exceeded(self):
        """Test that HTTPException is raised when IP limit exceeded."""
        from fastapi import HTTPException

        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user_id = str(uuid4())
        ip_address = "192.168.1.3"

        # Max out IP limit
        for i in range(20):
            await limiter.check_ip_limit(ip_address)

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_generation_limit(user_id, ip_address, "pro")

        assert exc_info.value.status_code == 429

        await limiter.close()

    @pytest.mark.asyncio
    async def test_redis_key_generation(self):
        """Test Redis key generation for different identifier types."""
        limiter = GenerationRateLimiter(redis_url=None)

        user_key = limiter._get_redis_key("user123", "user")
        ip_key = limiter._get_redis_key("192.168.1.1", "ip")

        assert user_key == "ratelimit:user:user123"
        assert ip_key == "ratelimit:ip:192.168.1.1"

    @pytest.mark.asyncio
    async def test_get_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns singleton instance."""
        from app.middleware.rate_limit import get_rate_limiter, shutdown_rate_limiter

        # Clean up any existing instance
        await shutdown_rate_limiter()

        limiter1 = await get_rate_limiter()
        limiter2 = await get_rate_limiter()

        assert limiter1 is limiter2, "Should return same instance"

        await shutdown_rate_limiter()

    @pytest.mark.asyncio
    async def test_shutdown_rate_limiter(self):
        """Test that shutdown_rate_limiter cleans up properly."""
        from app.middleware.rate_limit import get_rate_limiter, shutdown_rate_limiter, _rate_limiter

        await get_rate_limiter()
        await shutdown_rate_limiter()

        # Should be able to get a new instance after shutdown
        new_limiter = await get_rate_limiter()
        assert new_limiter is not None

        await shutdown_rate_limiter()

    @pytest.mark.asyncio
    async def test_pro_tier_bypasses_user_limit(self):
        """Test that pro tier completely bypasses user limit checks."""
        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user_id = str(uuid4())

        # Use different IPs to avoid IP limit (IP limit applies to all tiers)
        for i in range(30):
            ip_address = f"172.{i}.{uuid4().int % 255}.{uuid4().int % 255}"
            # Should not raise exception for pro tier
            await limiter.check_generation_limit(user_id, ip_address, "pro")

        await limiter.close()

    @pytest.mark.asyncio
    async def test_retry_after_calculation(self):
        """Test that retry_after is calculated correctly."""
        limiter = GenerationRateLimiter(redis_url=None)
        await limiter.connect()

        user_id = str(uuid4())

        # Max out limit
        for i in range(10):
            await limiter.check_user_limit(user_id, "free")

        # Next request should have retry_after > 0
        is_limited, retry_after = await limiter.check_user_limit(user_id, "free")
        assert is_limited
        assert retry_after > 0
        assert retry_after <= limiter.window_seconds

        await limiter.close()
