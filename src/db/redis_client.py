from redis.asyncio import Redis
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Global Redis client
_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """Get Redis client instance."""
    global _redis_client

    if _redis_client is None:
        _redis_client = Redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )

    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client connection."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


class RedisClient:
    """Redis client wrapper for session management and caching."""

    def __init__(self):
        self.client: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.client = await get_redis_client()

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        await close_redis_client()

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if self.client is None:
            await self.connect()
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        """Set value in Redis with optional expiration."""
        if self.client is None:
            await self.connect()
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        """Delete key from Redis."""
        if self.client is None:
            await self.connect()
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if self.client is None:
            await self.connect()
        return await self.client.exists(key) > 0
