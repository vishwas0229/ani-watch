import pytest

from ani_watch.domain.details import AnimeDetails
from ani_watch.metadata.service import AniListMetadataService


class FakeClient:
    async def execute(self, query, variables=None):
        if "Page(" in query:
            return {
                "Page": {
                    "media": [
                        {
                            "id": 100,
                            "title": {
                                "english": "Example",
                                "romaji": "Example Romaji",
                                "native": "例",
                            },
                        }
                    ]
                }
            }
        return {
            "Media": {
                "id": 100,
                "title": {
                    "english": "Example",
                    "romaji": "Example Romaji",
                    "native": "例",
                },
                "description": "Description",
                "status": "FINISHED",
                "format": "TV",
                "episodes": 12,
                "duration": 24,
                "averageScore": 88,
                "genres": ["Drama", "Fantasy"],
                "tags": [{"name": "Magic"}],
                "season": "FALL",
                "seasonYear": 2023,
                "coverImage": {"large": "https://example.test/cover.jpg"},
                "siteUrl": "https://anilist.co/anime/100",
                "isFavourite": True,
            }
        }


@pytest.mark.asyncio
async def test_metadata_service_maps_search_and_details() -> None:
    service = AniListMetadataService(FakeClient())
    results = await service.search("Example")
    assert results[0].anilist_id == 100
    details = await service.details(100)
    assert isinstance(details, AnimeDetails)
    assert details.genres == ("Drama", "Fantasy")
    assert details.tags == ("Magic",)
