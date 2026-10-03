"""Provider health monitoring and circuit breaking."""

from __future__ import annotations

import time
from dataclasses import dataclass

from ani_watch.domain.errors import ProviderError
from ani_watch.providers.contracts import MediaCandidate, Provider
from ani_watch.domain.models import AnimeRef, EpisodeRef


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


class CircuitBreaker:
    """Open a circuit after repeated provider failures."""

    def __init__(self, failure_threshold: int = 3, recovery_seconds: float = 60.0) -> None:
        self.failure_threshold = max(1, failure_threshold)
        self.recovery_seconds = max(1.0, recovery_seconds)
        self._states: dict[str, CircuitState] = {}

    def allow(self, provider: str) -> bool:
        state = self._states.setdefault(provider, CircuitState())
        if state.opened_at is None:
            return True
        if time.monotonic() - state.opened_at >= self.recovery_seconds:
            state.opened_at = None
            state.failures = 0
            return True
        return False

    def success(self, provider: str) -> None:
        self._states[provider] = CircuitState()

    def failure(self, provider: str) -> None:
        state = self._states.setdefault(provider, CircuitState())
        state.failures += 1
        if state.failures >= self.failure_threshold:
            state.opened_at = time.monotonic()


class ProviderHealth:
    """Track provider success/failure and expose health snapshots."""

    def __init__(self) -> None:
        self._stats: dict[str, dict[str, int]] = {}

    def success(self, provider: str) -> None:
        self._stats.setdefault(provider, {"successes": 0, "failures": 0})["successes"] += 1

    def failure(self, provider: str) -> None:
        self._stats.setdefault(provider, {"successes": 0, "failures": 0})["failures"] += 1

    def snapshot(self) -> dict[str, dict[str, int]]:
        return {name: values.copy() for name, values in self._stats.items()}


class ProviderResolver:
    """Resolve an episode with ordered fallback and circuit protection."""

    def __init__(
        self,
        providers: ProviderRegistry,
        *,
        health: ProviderHealth | None = None,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        self.providers = providers
        self.health = health or ProviderHealth()
        self.breaker = breaker or CircuitBreaker()

    async def resolve(
        self,
        anime: AnimeRef,
        episode: EpisodeRef,
        *,
        quality: str | None = None,
    ) -> MediaCandidate:
        last_error: Exception | None = None
        for provider in self.providers.ordered():
            if not self.breaker.allow(provider.name):
                continue
            try:
                if not await provider.available(anime, episode):
                    continue
                candidate = await provider.resolve(anime, episode, quality=quality)
                if candidate is None:
                    continue
                self.health.success(provider.name)
                self.breaker.success(provider.name)
                return candidate
            except Exception as exc:
                last_error = exc
                self.health.failure(provider.name)
                self.breaker.failure(provider.name)
        message = "No configured provider could resolve the episode."
        if last_error:
            message += f" Last error: {last_error}"
        raise ProviderError(message)
