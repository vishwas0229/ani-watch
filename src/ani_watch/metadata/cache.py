"""Metadata cache adapters."""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from typing import Any


class MemoryCache:
    """Bounded TTL cache for offline/degraded operation."""

    def __init__(self, max_entries: int = 256, ttl_seconds: int = 900) -> None:
        self.max_entries = max(1, max_entries)
        self.ttl_seconds = max(1, ttl_seconds)
        self._values: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        item = self._values.get(key)
        if item is None:
            return None
        expires, value = item
        if expires <= time.monotonic():
            self._values.pop(key, None)
            return None
        self._values.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        self._values[key] = (time.monotonic() + self.ttl_seconds, value)
        self._values.move_to_end(key)
        while len(self._values) > self.max_entries:
            self._values.popitem(last=False)


class RedisCache:
    """Optional Redis-backed cache using JSON values."""

    def __init__(self, url: str, ttl_seconds: int = 900) -> None:
        self.ttl_seconds = max(1, ttl_seconds)
        import redis

        self._client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Any | None:
        value = self._client.get(key)
        return json.loads(value) if value is not None else None

    def set(self, key: str, value: Any) -> None:
        self._client.setex(key, self.ttl_seconds, json.dumps(value, default=str))
