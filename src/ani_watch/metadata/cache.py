"""Cache-aware AniList metadata service."""

from __future__ import annotations

import dataclasses
import json

from ani_watch.cache.redis import RedisCache
from .service import AniListMetadataService


class CachedAniListMetadataService:
    """Add TTL caching and degraded-mode reads to metadata access."""

    def __init__(
        self,
        service: AniListMetadataService,
        cache: RedisCache,
    ) -> None:
        self.service = service
        self.cache = cache

    async def details(self, anime_id: int):
        key = "anilist:details:" + str(anime_id)
        cached = await self.cache.get_json(key)
        if cached:
            return self.service_to_details(cached)
        details = await self.service.details(anime_id)
        await self.cache.set_json(
            key,
            dataclasses.asdict(details),
        )
        return details

    async def search(self, query: str):
        key = "anilist:search:" + query.strip().lower()
        cached = await self.cache.get_json(key)
        if cached and isinstance(cached.get("items"), list):
            from ani_watch.domain.models import AnimeRef

            return [
                AnimeRef(anilist_id=int(item["anilist_id"]), title=str(item["title"]))
                for item in cached["items"]
            ]
        results = await self.service.search(query)
        await self.cache.set_json(
            key,
            {"items": [dataclasses.asdict(item) for item in results]},
        )
        return results

    async def episodes(self, anime_id: int):
        return await self.service.episodes(anime_id)

    @staticmethod
    def service_to_details(data: dict):
        from ani_watch.domain.details import AnimeDetails

        return AnimeDetails(**data)
