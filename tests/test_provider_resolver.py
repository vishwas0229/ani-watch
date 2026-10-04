import pytest

from ani_watch.domain.errors import ProviderError
from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.providers.registry import ProviderRegistry
from ani_watch.providers.resilience import ProviderResolver


class FakeProvider:
    def __init__(self, name: str) -> None:
        self.name = name
        self.available_calls = 0
        self.resolve_calls = 0

    async def available(self, anime, episode) -> bool:
        self.available_calls += 1
        return True

    async def resolve(self, anime, episode, *, quality=None):
        self.resolve_calls += 1
        return MediaCandidate(
            uri=f"https://media.example/{self.name}/{episode.number}.m3u8",
            provider=self.name,
            quality=quality,
        )


async def test_provider_resolver_can_target_one_provider() -> None:
    local = FakeProvider("local")
    online = FakeProvider("online")
    resolver = ProviderResolver(ProviderRegistry([local, online]))

    candidate = await resolver.resolve(
        AnimeRef(1, "Sample"),
        EpisodeRef(1, 2),
        quality="720p",
        provider_name="online",
    )

    assert candidate.provider == "online"
    assert candidate.quality == "720p"
    assert local.resolve_calls == 0
    assert online.resolve_calls == 1


async def test_provider_resolver_rejects_unknown_target_provider() -> None:
    resolver = ProviderResolver(ProviderRegistry())

    with pytest.raises(ProviderError, match="not configured"):
        await resolver.resolve(
            AnimeRef(1, "Sample"),
            EpisodeRef(1, 1),
            provider_name="online",
        )
