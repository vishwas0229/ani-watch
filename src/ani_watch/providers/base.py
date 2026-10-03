"""Provider contracts and status types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.models import AnimeRef
from ani_watch.infra.resilience import CircuitBreaker


@dataclass(frozen=True, slots=True)
class ProviderHealth:
    """Current health snapshot for one provider."""

    name: str
    healthy: bool
    failures: int


class EpisodeProvider(ABC):
    """Base class for an episode source adapter."""

    name: str

    def __init__(self, failure_threshold: int = 3, recovery_seconds: int = 60) -> None:
        self.breaker = CircuitBreaker(failure_threshold, recovery_seconds)

    @abstractmethod
    async def episodes(self, anime: AnimeRef) -> list[EpisodeItem]:
        """List playable or resolvable episodes."""

    @abstractmethod
    async def resolve(self, anime: AnimeRef, episode_number: int) -> EpisodeItem:
        """Resolve one episode."""

    def health(self) -> ProviderHealth:
        """Return current circuit state."""
        return ProviderHealth(
            name=self.name,
            healthy=self.breaker.allow(),
            failures=self.breaker.failures,
        )
