from ani_watch.domain.errors import OfflineError
from ani_watch.metadata.cache import MemoryCache
from ani_watch.metadata.cached import CachedMetadataService


class FakeMetadataClient:
    def __init__(self) -> None:
        self.search_calls = 0
        self.details_calls = 0
        self.close_calls = 0

    async def search(self, query: str, limit: int = 10):
        self.search_calls += 1
        return [
            {
                "id": 7,
                "title": {
                    "english": query.title(),
                    "romaji": query.title(),
                },
            }
        ]

    async def details(self, anime_id: int):
        self.details_calls += 1
        return {
            "id": anime_id,
            "title": {"english": "Cached Anime"},
            "episodes": 12,
            "averageScore": 90,
            "genres": ["Drama"],
        }

    async def close(self):
        self.close_calls += 1


async def test_cached_service_reuses_search_results() -> None:
    client = FakeMetadataClient()
    service = CachedMetadataService(client, cache=MemoryCache())

    first = await service.search("frieren")
    second = await service.search("frieren")

    assert first == second
    assert client.search_calls == 1


async def test_cached_service_reuses_details() -> None:
    client = FakeMetadataClient()
    service = CachedMetadataService(client, cache=MemoryCache())

    first = await service.details(7)
    second = await service.details(7)

    assert first == second
    assert client.details_calls == 1


async def test_offline_mode_uses_cached_search_without_network() -> None:
    cache = MemoryCache()
    online_client = FakeMetadataClient()
    online = CachedMetadataService(online_client, cache=cache)

    expected = await online.search("frieren")

    offline_client = FakeMetadataClient()
    offline = CachedMetadataService(offline_client, cache=cache, offline=True)
    result = await offline.search("frieren")

    assert result == expected
    assert offline_client.search_calls == 0


async def test_offline_mode_reports_uncached_requests() -> None:
    service = CachedMetadataService(
        FakeMetadataClient(),
        cache=MemoryCache(),
        offline=True,
    )

    try:
        await service.search("unknown")
    except OfflineError as exc:
        assert "not cached locally" in str(exc)
    else:
        raise RuntimeError("Expected OfflineError for an uncached offline search")


async def test_cached_service_closes_its_client_once() -> None:
    client = FakeMetadataClient()
    service = CachedMetadataService(client)

    await service.close()

    assert client.close_calls == 1
