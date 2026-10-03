"""Provider registry, discovery, fallback, and health monitoring."""

from __future__ import annotations

from collections.abc import Iterable

from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.models import AnimeRef
from ani_watch.infra.resilience import CircuitOpenError
from .base import EpisodeProvider, ProviderHealth


class ProviderRegistry:
    """Manage configured providers and resolve through healthy fallbacks."""

    def __init__(self, providers: Iterable[EpisodeProvider] = ()) -> None:
        self._providers: dict[str, EpisodeProvider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: EpisodeProvider) -> None:
        """Register or replace one provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> EpisodeProvider:
        """Return one registered provider."""
        try:
            return self._providers[name]
        except KeyError as exc:
            raise KeyError(f"Provider {name!r} is not configured.") from exc

    def discover(self) -> list[str]:
        """List configured provider names."""
        return list(self._providers)

    def health(self) -> list[ProviderHealth]:
        """Return health state for every provider."""
        return [provider.health() for provider in self._providers.values()]

    async def resolve(
        self,
        anime: AnimeRef,
        episode_number: int,
        preferred: Iterable[str] | None = None,
    ) -> EpisodeItem:
        """Resolve using configured order and automatic fallback."""
        names = tuple(preferred or self._providers.keys())
        errors: list[str] = []

        for name in names:
            provider = self._providers.get(name)
            if provider is None:
                errors.append(f"{name}: not configured")
                continue
            if not provider.breaker.allow():
                errors.append(f"{name}: circuit open")
                continue

            try:
                result = await provider.resolve(anime, episode_number)
            except Exception as exc:
                provider.breaker.failure()
                errors.append(f"{name}: {exc}")
                continue

            provider.breaker.success()
            return result

        raise CircuitOpenError(
            "No configured provider could resolve the episode. " + "; ".join(errors)
        )
