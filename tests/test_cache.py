import pytest

from ani_watch.domain.details import AnimeDetails
from ani_watch.metadata.cache import CachedAniListMetadataService


class FakeMetadata:
    async def details(self, anime_id: int):
        return AnimeDetails(anilist_id=anime_id, title="Example", genres=("Drama",))

    async def search(self, query: str):
        from ani_watch.domain.models import AnimeRef
        return [AnimeRef(1, "Example")]


class FakeCache:
    def __init__(self):
        self.data = {}

    async def get_json(self, key):
        return self.data.get(key)

    async def set_json(self, key, value):
        self.data[key] = value


@pytest.mark.asyncio
async def test_cached_metadata_reuses_details() -> None:
    cache = FakeCache()
    service = CachedAniListMetadataService(FakeMetadata(), cache)

    first = await service.details(1)
    second = await service.details(1)

    assert first.title == "Example"
    assert second.anilist_id == 1
    assert len(cache.data) == 1


@pytest.mark.asyncio
async def test_cached_metadata_reuses_search_results() -> None:
    cache = FakeCache()
    service = CachedAniListMetadataService(FakeMetadata(), cache)

    results = await service.search("Example")
    cached = await service.search("Example")

    assert results[0].title == "Example"
    assert cached[0].anilist_id == 1
