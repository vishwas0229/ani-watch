"""Caching facade for AniList metadata."""

from __future__ import annotations

from typing import Any

from ani_watch.domain.errors import OfflineError
from ani_watch.domain.models import AnimeDetails, AnimeRef, EpisodeItem
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

    async def close(self) -> None:
        """Close the underlying metadata client."""
        await self.client.close()

    async def search(self, query: str, limit: int = 10) -> list[AnimeRef]:
        key = f"search:{query.strip().lower()}:{limit}"
        cached = self.cache.get(key)
        if cached is not None:
            return [AnimeRef(**item) for item in cached]

        if self.offline:
            raise OfflineError("Offline mode is enabled and this search is not cached locally.")

        results = await self.client.search(query, limit=limit)
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
            raise OfflineError(
                "Offline mode is enabled and these anime details are not cached locally."
            )

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
        self.cache.set(
            key,
            {
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
            },
        )
        return details

    async def episode_items(self, anime_id: int) -> list[EpisodeItem]:
        """Return cached/provider-neutral episode rows for one anime."""
        key = f"episodes:{anime_id}"
        cached = self.cache.get(key)
        if cached is not None:
            return [EpisodeItem(**item) for item in cached]

        if self.offline:
            raise OfflineError(
                "Offline mode is enabled and these episode details are not cached locally."
            )

        first_page = await self.client.episodes(anime_id, page=1, limit=25)
        status = self._text(first_page.get("status"))
        total = self._int(first_page.get("episodes"))
        duration = self._int(first_page.get("duration"))
        schedule = first_page.get("airingSchedule") or {}
        if not isinstance(schedule, dict):
            schedule = {}

        scheduled = self._episode_numbers(schedule.get("nodes"))
        has_next = bool((schedule.get("pageInfo") or {}).get("hasNextPage"))

        page = 2
        while has_next:
            next_page = await self.client.episodes(anime_id, page=page, limit=25)
            next_schedule = next_page.get("airingSchedule") or {}
            if not isinstance(next_schedule, dict):
                break
            scheduled.update(self._episode_numbers(next_schedule.get("nodes")))
            has_next = bool((next_schedule.get("pageInfo") or {}).get("hasNextPage"))
            page += 1

        if total is not None and total > 0:
            numbers = range(1, total + 1)
            available_numbers = (
                set(numbers)
                if status == "FINISHED" or len(scheduled) >= total
                else scheduled
            )
        else:
            numbers = sorted(scheduled)
            available_numbers = set(numbers)

        episodes = [
            EpisodeItem(
                number=number,
                title=None,
                duration_minutes=duration,
                available=number in available_numbers,
            )
            for number in numbers
            if number > 0
        ]
        self.cache.set(
            key,
            [
                {
                    "number": episode.number,
                    "title": episode.title,
                    "duration_minutes": episode.duration_minutes,
                    "watched": episode.watched,
                    "available": episode.available,
                }
                for episode in episodes
            ],
        )
        return episodes

    @classmethod
    def _episode_numbers(cls, nodes: Any) -> set[int]:
        """Extract positive numeric episode numbers and ignore specials."""
        return {
            number
            for node in nodes or []
            if isinstance(node, dict)
            for number in (cls._int(node.get("episode")),)
            if number is not None and number > 0
        }

    @staticmethod
    def _title(value: Any) -> str:
        return (
            str((value or {}).get("english") or "").strip()
            or str((value or {}).get("romaji") or "").strip()
            or "Unknown anime"
        )

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
