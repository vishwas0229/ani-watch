import httpx
import pytest

from ani_watch.domain.errors import MetadataError, RateLimitError
from ani_watch.metadata.anilist import AniListClient
from ani_watch.metadata.cache import MemoryCache
from ani_watch.metadata.cached import CachedMetadataService
from ani_watch.metadata.service import AnimeMetadataService


async def test_anilist_search_parses_graphql_payload() -> None:
    responses = [
        httpx.Response(
            200,
            json={
                "data": {
                    "Page": {
                        "media": [
                            {
                                "id": 1,
                                "title": {
                                    "english": "Sample",
                                    "romaji": "Sample",
                                    "native": "サンプル",
                                },
                            }
                        ]
                    }
                }
            },
        )
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "graphql.anilist.co"
        return responses.pop(0)

    client = AniListClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    service = AnimeMetadataService(client)

    result = await service.search("Sample")
    assert result[0].anilist_id == 1
    assert result[0].title == "Sample"


async def test_anilist_details_maps_metadata() -> None:
    payload = {
        "data": {
            "Media": {
                "id": 2,
                "title": {"english": "Details", "native": "詳細"},
                "description": "Description",
                "format": "TV",
                "status": "FINISHED",
                "episodes": 12,
                "averageScore": 88,
                "genres": ["Drama", "Fantasy"],
                "season": "WINTER",
                "seasonYear": 2024,
            }
        }
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = AniListClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    service = AnimeMetadataService(client)

    details = await service.details(2)
    assert details.title == "Details"
    assert details.native_title == "詳細"
    assert details.score == 88.0
    assert details.genres == ("Drama", "Fantasy")


async def test_anilist_episodes_map_known_episode_count() -> None:
    payload = {
        "data": {
            "Media": {
                "id": 2,
                "episodes": 3,
                "duration": 24,
                "airingSchedule": {
                    "nodes": [{"episode": 1}, {"episode": 2}, {"episode": 0}],
                    "pageInfo": {"hasNextPage": False},
                },
            }
        }
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = AniListClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    service = AnimeMetadataService(client)

    episodes = await service.episode_items(2)

    assert [episode.number for episode in episodes] == [1, 2, 3]
    assert all(episode.title is None for episode in episodes)
    assert all(episode.duration_minutes == 24 for episode in episodes)
    assert all(episode.available for episode in episodes)


async def test_anilist_episodes_use_schedule_when_count_is_missing() -> None:
    responses = [
        httpx.Response(
            200,
            json={
                "data": {
                    "Media": {
                        "id": 3,
                        "episodes": None,
                        "duration": None,
                        "airingSchedule": {
                            "nodes": [{"episode": 2}, {"episode": 1}, {"episode": 0}],
                            "pageInfo": {"hasNextPage": False},
                        },
                    }
                }
            },
        )
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    client = AniListClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    service = AnimeMetadataService(client)

    episodes = await service.episode_items(3)

    assert [episode.number for episode in episodes] == [1, 2]
    assert all(episode.duration_minutes is None for episode in episodes)


async def test_anilist_episodes_page_through_schedule_when_count_unknown() -> None:
    payloads = [
        {
            "data": {
                "Media": {
                    "id": 4,
                    "episodes": None,
                    "duration": 23,
                    "airingSchedule": {
                        "nodes": [{"episode": 2}],
                        "pageInfo": {"hasNextPage": True},
                    },
                }
            }
        },
        {
            "data": {
                "Media": {
                    "id": 4,
                    "episodes": None,
                    "duration": 23,
                    "airingSchedule": {
                        "nodes": [{"episode": 27}, {"episode": 1}],
                        "pageInfo": {"hasNextPage": False},
                    },
                }
            }
        },
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        response = payloads.pop(0)
        return httpx.Response(200, json=response)

    client = AniListClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    service = AnimeMetadataService(client)

    episodes = await service.episode_items(4)

    assert [episode.number for episode in episodes] == [1, 2, 27]
    assert all(episode.duration_minutes == 23 for episode in episodes)



async def test_cached_metadata_service_caches_episode_items() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "data": {
                    "Media": {
                        "id": 9,
                        "episodes": 2,
                        "duration": 24,
                        "airingSchedule": {
                            "nodes": [{"episode": 1}, {"episode": 2}],
                            "pageInfo": {"hasNextPage": False},
                        },
                    }
                }
            },
        )

    client = AniListClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    service = CachedMetadataService(client, cache=MemoryCache())

    first = await service.episode_items(9)
    second = await service.episode_items(9)

    assert [episode.number for episode in first] == [1, 2]
    assert [episode.number for episode in second] == [1, 2]
    assert calls == 1

    await service.close()


async def test_anilist_graphql_errors_raise_metadata_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "bad query"}]})

    client = AniListClient(
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        retries=0,
    )

    with pytest.raises(MetadataError, match="bad query"):
        await client.search("x")


async def test_anilist_rate_limit_raises_after_retries() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    client = AniListClient(
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        retries=0,
    )

    with pytest.raises(RateLimitError):
        await client.search("x")
