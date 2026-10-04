"""Provider-neutral metadata service."""

from __future__ import annotations

from typing import Any

from ani_watch.domain.models import AnimeDetails, AnimeRef, EpisodeItem
from ani_watch.metadata.anilist import AniListClient


class AnimeMetadataService:
    """Translate AniList payloads into stable domain objects."""

    def __init__(self, client: AniListClient) -> None:
        self.client = client

    async def search(self, query: str, limit: int = 10) -> list[AnimeRef]:
        results = await self.client.search(query, limit=limit)
        return [
            AnimeRef(
                anilist_id=int(item["id"]),
                title=self._title(item.get("title")),
            )
            for item in results
            if item.get("id")
        ]

    async def details(self, anime_id: int) -> AnimeDetails:
        item = await self.client.details(anime_id)
        return AnimeDetails(
            anilist_id=int(item["id"]),
            title=self._title(item.get("title")),
            native_title=self._text(item.get("title", {}).get("native")),
            description=self._text(item.get("description")),
            status=self._text(item.get("status")),
            episodes=self._int(item.get("episodes")),
            score=self._float(item.get("averageScore")),
            genres=tuple(
                value.strip()
                for value in item.get("genres", [])
                if isinstance(value, str) and value.strip()
            ),
            season=self._text(item.get("season")),
            year=self._int(item.get("seasonYear")),
            format=self._text(item.get("format")),
        )

    async def episode_items(self, anime_id: int) -> list[EpisodeItem]:
        """Return stable episode rows from AniList metadata."""
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
            page_info = next_schedule.get("pageInfo") or {}
            has_next = bool(page_info.get("hasNextPage"))
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

        return [
            EpisodeItem(
                number=number,
                # AniList exposes a general duration for the anime, not a
                # stable per-episode title in this mapping.
                title=None,
                duration_minutes=duration,
                available=number in available_numbers,
            )
            for number in numbers
            if number > 0
        ]

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
        if not isinstance(value, dict):
            return "Unknown anime"
        return (
            str(value.get("english") or "").strip()
            or str(value.get("romaji") or "").strip()
            or str(value.get("native") or "").strip()
            or "Unknown anime"
        )

    @staticmethod
    def _text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
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
