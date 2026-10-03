import asyncio

from ani_watch.domain.models import AnimeRef
from ani_watch.infra.resilience import CircuitBreaker, CircuitOpenError
from ani_watch.providers.base import EpisodeProvider
from ani_watch.providers.registry import ProviderRegistry


class FailingProvider(EpisodeProvider):
    name = "failing"

    async def episodes(self, anime: AnimeRef):
        raise RuntimeError("unavailable")

    async def resolve(self, anime: AnimeRef, episode_number: int):
        raise RuntimeError("unavailable")


def test_circuit_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=60)
    assert breaker.allow()
    breaker.failure()
    assert breaker.allow()
    breaker.failure()
    assert not breaker.allow()


def test_provider_registry_surfaces_failure_details() -> None:
    async def run():
        registry = ProviderRegistry([FailingProvider(failure_threshold=1)])
        try:
            await registry.resolve(AnimeRef(1, "Example"), 1)
        except CircuitOpenError as exc:
            assert "failing" in str(exc)
        else:
            raise AssertionError("expected CircuitOpenError")

    asyncio.run(run())
