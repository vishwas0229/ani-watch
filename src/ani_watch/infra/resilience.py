"""Reliability primitives shared by providers and network adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import monotonic


class CircuitOpenError(RuntimeError):
    """Raised when a provider circuit is open."""


@dataclass(slots=True)
class CircuitBreaker:
    """Simple closed/open/half-open circuit breaker."""

    failure_threshold: int = 3
    recovery_seconds: int = 60
    failures: int = 0
    opened_at: float | None = None

    def allow(self) -> bool:
        """Return whether another call may be attempted."""
        if self.opened_at is None:
            return True
        if monotonic() - self.opened_at >= self.recovery_seconds:
            self.opened_at = None
            self.failures = 0
            return True
        return False

    def success(self) -> None:
        """Reset the circuit after a successful call."""
        self.failures = 0
        self.opened_at = None

    def failure(self) -> None:
        """Record one failure and open the circuit when necessary."""
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = monotonic()


async def with_retries(
    operation: Callable[[], Awaitable[object]],
    retries: int = 2,
    base_delay: float = 0.5,
) -> object:
    """Retry transient operations with exponential backoff."""
    for attempt in range(max(0, retries) + 1):
        try:
            return await operation()
        except Exception:
            if attempt >= retries:
                raise
            await asyncio.sleep(base_delay * (2**attempt))
    raise RuntimeError("Unreachable")
