"""Caching facade for AniList metadata."""

from __future__ import annotations

from typing import Any

from ani_watch.domain.models import AnimeDetails
from ani_watch.domain.models import AnimeRef
from ani_watch.metadata.anilist import AniListClient
from ani_watch.metadata.cache import MemoryCache, RedisCache


class CachedMetadataService:
    """Cache searches/details and provide degraded-mode behavior."""

    def __init__(
        self,
        client: AniListClient,
        *,
        cache: MemoryCache | RedisCache | None = None,
        offline: bool = False,
    ) -> None:
        self.client = client
        self.cache = cache or MemoryCache()
        self.offline = offline

    async def search(self, query: str) -> list[AnimeRef]:
        key = f"search:{query.strip().lower()}"
        cached = self.cache.get(key)
        if cached is not None:
            return [AnimeRef(**item) for item in cached]

        if self.offline:
            return []

        results = await self.client.search(query)
        refs = [
            AnimeRef(
                anilist_id=int(item["id"]),
                title=self._title(item.get("title")),
            )
            for item in results
            if item.get("id")
        ]
        self.cache.set(
            key,
            [{"anilist_id": item.anilist_id, "title": item.title} for item in refs],
        )
        return refs

    async def details(self, anime_id: int) -> AnimeDetails:
        key = f"details:{anime_id}"
        cached = self.cache.get(key)
        if cached is not None:
            return AnimeDetails(**cached)

        if self.offline:
            raise LookupError("Anime details are not cached and offline mode is enabled.")

        item = await self.client.details(anime_id)
        details = AnimeDetails(
            anilist_id=int(item["id"]),
            title=self._title(item.get("title")),
            native_title=self._text(item.get("title", {}).get("native")),
            description=self._text(item.get("description")),
            status=self._text(item.get("status")),
            episodes=self._int(item.get("episodes")),
            score=self._float(item.get("averageScore")),
            genres=tuple(x.strip() for x in item.get("genres", []) if x and x.strip()),
            season=self._text(item.get("season")),
            year=self._int(item.get("seasonYear")),
            format=self._text(item.get("format")),
        )
        self.cache.set(key, details.__dict__ if hasattr(details, "__dict__") else {
            "anilist_id": details.anilist_id,
            "title": details.title,
            "native_title": details.native_title,
            "description": details.description,
            "status": details.status,
            "episodes": details.episodes,
            "score": details.score,
            "genres": details.genres,
            "season": details.season,
            "year": details.year,
            "format": details.format,
            "is_favorite": details.is_favorite,
        })
        return details

    @staticmethod
    def _title(value: Any) -> str:
        return str((value or {}).get("english") or (value or {}).get("romaji") or "Unknown anime")

    @staticmethod
    def _text(value: Any) -> str | None:
        text = str(value).strip() if value is not None else ""
        return text or None

    @staticmethod
    def _int(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _float(value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
