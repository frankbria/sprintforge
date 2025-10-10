"""
Rate limiting middleware for Excel generation and API endpoints.

This module implements:
- Per-user rate limits (10 generations/hour for free tier, unlimited for pro)
- Per-IP rate limits (20 generations/hour to prevent abuse)
- Redis-based distributed rate limiting
- Proper HTTP 429 responses with Retry-After headers
"""

import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import structlog
import redis.asyncio as redis

from app.core.config import settings

logger = structlog.get_logger(__name__)


class GenerationRateLimiter:
    """
    Rate limiter for Excel generation endpoints.

    Implements:
    - User-based limits: 10/hour for free tier, unlimited for pro
    - IP-based limits: 20/hour to prevent anonymous abuse
    - Redis-backed for distributed systems
    - Graceful fallback to in-memory if Redis unavailable
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL. Uses settings.redis_url if not provided.
        """
        self.redis_url = redis_url or settings.redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_store: Dict[str, list] = {}

        # Rate limit configuration
        self.free_tier_limit = 10  # requests per hour
        self.ip_limit = 20  # requests per hour
        self.window_seconds = 3600  # 1 hour

    async def connect(self):
        """Establish Redis connection."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.warning(
                "Failed to connect to Redis, using in-memory store",
                error=str(e)
            )
            self.redis_client = None

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiter disconnected from Redis")

    def _get_redis_key(self, identifier: str, limit_type: str) -> str:
        """
        Generate Redis key for rate limit tracking.

        Args:
            identifier: User ID or IP address
            limit_type: Type of limit (user, ip)

        Returns:
            Redis key string
        """
        return f"ratelimit:{limit_type}:{identifier}"

    async def _check_redis_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, int]:
        """
        Check rate limit using Redis.

        Args:
            key: Redis key
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        if not self.redis_client:
            return await self._check_memory_limit(key, limit, window)

        try:
            now = time.time()
            window_start = now - window

            # Remove old entries outside the window
            await self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            count = await self.redis_client.zcard(key)

            if count >= limit:
                # Get oldest request time to calculate retry-after
                oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int((oldest_time + window) - now)
                    return True, max(retry_after, 1)
                return True, window

            # Add current request
            await self.redis_client.zadd(key, {str(now): now})

            # Set expiration on key
            await self.redis_client.expire(key, window)

            return False, 0

        except Exception as e:
            logger.error("Redis rate limit check failed", error=str(e))
            # Fallback to in-memory
            return await self._check_memory_limit(key, limit, window)

    async def _check_memory_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, int]:
        """
        Check rate limit using in-memory store (fallback).

        Args:
            key: Identifier key
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window

        # Initialize if not exists
        if key not in self.in_memory_store:
            self.in_memory_store[key] = []

        # Remove old entries
        self.in_memory_store[key] = [
            ts for ts in self.in_memory_store[key]
            if ts > window_start
        ]

        if len(self.in_memory_store[key]) >= limit:
            oldest = min(self.in_memory_store[key])
            retry_after = int((oldest + window) - now)
            return True, max(retry_after, 1)

        # Add current request
        self.in_memory_store[key].append(now)

        return False, 0

    async def check_user_limit(
        self,
        user_id: str,
        subscription_tier: str = "free"
    ) -> Tuple[bool, int]:
        """
        Check user-based rate limit.

        Args:
            user_id: User identifier
            subscription_tier: User subscription tier (free, pro, enterprise)

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        # Pro and enterprise tiers have no limits
        if subscription_tier in ["pro", "enterprise"]:
            return False, 0

        key = self._get_redis_key(user_id, "user")
        return await self._check_redis_limit(
            key,
            self.free_tier_limit,
            self.window_seconds
        )

    async def check_ip_limit(self, ip_address: str) -> Tuple[bool, int]:
        """
        Check IP-based rate limit.

        Args:
            ip_address: Client IP address

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        key = self._get_redis_key(ip_address, "ip")
        return await self._check_redis_limit(
            key,
            self.ip_limit,
            self.window_seconds
        )

    async def check_generation_limit(
        self,
        user_id: str,
        ip_address: str,
        subscription_tier: str = "free"
    ) -> None:
        """
        Check if generation request should be rate limited.

        Args:
            user_id: User identifier
            ip_address: Client IP address
            subscription_tier: User subscription tier

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Check user limit first
        user_limited, user_retry = await self.check_user_limit(
            user_id, subscription_tier
        )

        if user_limited:
            logger.warning(
                "User rate limit exceeded",
                user_id=user_id,
                tier=subscription_tier,
                retry_after=user_retry
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Generation rate limit exceeded. Free tier allows {self.free_tier_limit} generations per hour.",
                    "retry_after": user_retry,
                    "upgrade_url": "/pricing",  # Link to upgrade page
                }
            )

        # Check IP limit
        ip_limited, ip_retry = await self.check_ip_limit(ip_address)

        if ip_limited:
            logger.warning(
                "IP rate limit exceeded",
                ip_address=ip_address,
                retry_after=ip_retry
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests from this IP. Limit is {self.ip_limit} requests per hour.",
                    "retry_after": ip_retry,
                }
            )


# Global rate limiter instance
_rate_limiter: Optional[GenerationRateLimiter] = None


async def get_rate_limiter() -> GenerationRateLimiter:
    """
    Get or create the global rate limiter instance.

    Returns:
        GenerationRateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = GenerationRateLimiter()
        await _rate_limiter.connect()

    return _rate_limiter


async def shutdown_rate_limiter():
    """Shutdown the global rate limiter instance."""
    global _rate_limiter

    if _rate_limiter is not None:
        await _rate_limiter.close()
        _rate_limiter = None
