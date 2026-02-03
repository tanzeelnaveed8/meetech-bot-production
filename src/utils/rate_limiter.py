from typing import Optional
from datetime import datetime, timedelta
from src.db.redis_client import RedisClient


class RateLimiter:
    """Rate limiter using Redis for tracking request counts."""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client

    async def is_rate_limited(
        self,
        identifier: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if identifier is rate limited.

        Args:
            identifier: Unique identifier (e.g., phone number)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if rate limited, False otherwise
        """
        key = f"ratelimit:{identifier}"

        # Get current count
        count_str = await self.redis.get(key)
        count = int(count_str) if count_str else 0

        if count >= max_requests:
            return True

        # Increment count
        if count == 0:
            # First request in window, set with expiration
            await self.redis.set(key, "1", ex=window_seconds)
        else:
            # Increment existing count
            await self.redis.client.incr(key)

        return False

    async def get_remaining_requests(
        self,
        identifier: str,
        max_requests: int = 10
    ) -> int:
        """Get remaining requests for identifier."""
        key = f"ratelimit:{identifier}"
        count_str = await self.redis.get(key)
        count = int(count_str) if count_str else 0
        return max(0, max_requests - count)

    async def reset_limit(self, identifier: str) -> None:
        """Reset rate limit for identifier."""
        key = f"ratelimit:{identifier}"
        await self.redis.delete(key)


async def check_rate_limit(phone_number: str) -> bool:
    """
    Convenience function to check rate limit for a phone number.

    Returns:
        True if rate limited, False otherwise
    """
    redis_client = RedisClient()
    await redis_client.connect()

    rate_limiter = RateLimiter(redis_client)
    is_limited = await rate_limiter.is_rate_limited(
        phone_number,
        max_requests=10,  # 10 messages per minute per constitution
        window_seconds=60
    )

    return is_limited
