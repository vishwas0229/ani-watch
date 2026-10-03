"""Provider-neutral metadata service."""

from __future__ import annotations

from typing import Any

from ani_watch.domain.models import AnimeDetails
from ani_watch.domain.models import AnimeRef
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
