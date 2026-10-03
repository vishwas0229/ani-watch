import httpx
import pytest

from ani_watch.domain.errors import MetadataError, RateLimitError
from ani_watch.metadata.anilist import AniListClient
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
