"""Optional Redis cache adapter."""

from __future__ import annotations

import json
from typing import Any


class RedisCache:
    """Best-effort async Redis cache with graceful disabled mode."""

    def __init__(self, url: str | None, ttl_seconds: int = 900) -> None:
        self.url = url
        self.ttl_seconds = ttl_seconds
        self._redis: Any = None

        if not url:
            return
        try:
            import redis.asyncio as redis
        except ImportError:
            return
        self._redis = redis.from_url(url, decode_responses=True)

    @property
    def enabled(self) -> bool:
        """Whether a Redis client is available."""
        return self._redis is not None

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Read JSON data from cache."""
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    async def set_json(self, key: str, value: dict[str, Any]) -> None:
        """Write JSON data to cache, ignoring cache failures."""
        if not self._redis:
            return
        try:
            await self._redis.set(key, json.dumps(value), ex=self.ttl_seconds)
        except Exception:
            return

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis:
            await self._redis.aclose()
