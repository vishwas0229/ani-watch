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
    """Redis-backed cache with an in-process fallback and failure cooldown."""

    def __init__(
        self,
        url: str,
        ttl_seconds: int = 900,
        *,
        failure_cooldown_seconds: float = 30.0,
        client: Any | None = None,
        fallback: MemoryCache | None = None,
    ) -> None:
        self.ttl_seconds = max(1, ttl_seconds)
        self.failure_cooldown_seconds = max(1.0, failure_cooldown_seconds)
        self._fallback = fallback or MemoryCache(ttl_seconds=self.ttl_seconds)
        self._disabled_until = 0.0

        import redis

        self._redis = redis
        self._client = client or redis.Redis.from_url(url, decode_responses=True)

    def _backend_available(self) -> bool:
        return time.monotonic() >= self._disabled_until

    def _trip(self) -> None:
        self._disabled_until = time.monotonic() + self.failure_cooldown_seconds

    def _record_backend_success(self) -> None:
        self._disabled_until = 0.0

    def _restore_fallback(self, key: str, value: Any | None) -> None:
        """Best-effort write of a fallback value after a Redis miss/corruption."""
        if value is None or not self._backend_available():
            return
        try:
            payload = json.dumps(value, default=str)
            self._client.setex(key, self.ttl_seconds, payload)
            self._record_backend_success()
        except self._redis.RedisError:
            self._trip()
        except (TypeError, ValueError):
            return

    def get(self, key: str) -> Any | None:
        fallback_value = self._fallback.get(key)

        if not self._backend_available():
            return fallback_value

        try:
            value = self._client.get(key)
        except self._redis.RedisError:
            self._trip()
            return fallback_value

        if value is None:
            self._restore_fallback(key, fallback_value)
            return fallback_value

        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            self._restore_fallback(key, fallback_value)
            return fallback_value

        self._record_backend_success()
        self._fallback.set(key, parsed)
        return parsed

    def set(self, key: str, value: Any) -> None:
        self._fallback.set(key, value)

        if not self._backend_available():
            return

        try:
            payload = json.dumps(value, default=str)
            self._client.setex(key, self.ttl_seconds, payload)
            self._record_backend_success()
        except self._redis.RedisError:
            self._trip()
        except (TypeError, ValueError):
            return
