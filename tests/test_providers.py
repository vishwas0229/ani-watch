import asyncio

import pytest

from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.domain.errors import ProviderError
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.providers.registry import ProviderRegistry
from ani_watch.providers.resilience import CircuitBreaker, ProviderHealth, ProviderResolver


class GoodProvider:
    name = "good"

    async def available(self, anime, episode):
        return True

    async def resolve(self, anime, episode, *, quality=None):
        return MediaCandidate(uri="file:///episode.mp4", provider=self.name, quality=quality)


class BadProvider:
    name = "bad"

    async def available(self, anime, episode):
        return True

    async def resolve(self, anime, episode, *, quality=None):
        raise RuntimeError("provider down")


@pytest.mark.asyncio
async def test_provider_resolver_falls_back_to_good_provider() -> None:
    registry = ProviderRegistry([BadProvider(), GoodProvider()])
    resolver = ProviderResolver(registry)

    result = await resolver.resolve(
        AnimeRef(1, "Sample"),
        EpisodeRef(1, 1),
        quality="1080p",
    )

    assert result.provider == "good"
    assert resolver.health.snapshot()["bad"]["failures"] == 1


@pytest.mark.asyncio
async def test_provider_resolver_reports_no_provider() -> None:
    registry = ProviderRegistry([BadProvider()])
    resolver = ProviderResolver(
        registry,
        breaker=CircuitBreaker(failure_threshold=1, recovery_seconds=30),
        health=ProviderHealth(),
    )

    with pytest.raises(ProviderError):
        await resolver.resolve(AnimeRef(1, "Sample"), EpisodeRef(1, 1))

    with pytest.raises(ProviderError):
        await resolver.resolve(AnimeRef(1, "Sample"), EpisodeRef(1, 1))


def test_registry_rejects_blank_provider_name() -> None:
    class Empty:
        name = " "

    registry = ProviderRegistry()
    with pytest.raises(ValueError):
        registry.register(Empty())
