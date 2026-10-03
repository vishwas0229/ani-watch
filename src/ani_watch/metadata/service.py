"""AniList metadata service."""

from __future__ import annotations

from ani_watch.domain.details import AnimeDetails
from ani_watch.domain.errors import MetadataError
from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.models import AnimeRef

from .client import AniListClient


_MEDIA_FIELDS = """
id
title { romaji english native }
description(asHtml: false)
status
format
episodes
duration
averageScore
genres
tags { name }
season
seasonYear
coverImage { large }
siteUrl
isFavourite
"""


class AniListMetadataService:
    """Map AniList GraphQL responses into stable domain objects."""

    def __init__(self, client: AniListClient) -> None:
        self.client = client

    async def search(self, query: str, page: int = 1, per_page: int = 10) -> list[AnimeRef]:
        """Search anime by title and return stable references."""
        clean = query.strip()
        if not clean:
            return []
        result = await self.client.execute(
            f"""
            query Search($search: String, $page: Int, $perPage: Int) {{
              Page(page: $page, perPage: $perPage) {{
                media(search: $search, type: ANIME, sort: SEARCH_MATCH) {{
                  id
                  title {{ romaji english native }}
                }}
              }}
            }}
            """,
            {"search": clean, "page": page, "perPage": per_page},
        )
        media = result.get("Page", {}).get("media", [])
        refs: list[AnimeRef] = []
        for item in media:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            title = self._title(item.get("title", {}))
            refs.append(AnimeRef(anilist_id=int(item["id"]), title=title))
        return refs

    async def details(self, anime_id: int) -> AnimeDetails:
        """Fetch one anime's metadata."""
        result = await self.client.execute(
            f"""
            query Details($id: Int) {{
              Media(id: $id, type: ANIME) {{
                {_MEDIA_FIELDS}
              }}
            }}
            """,
            {"id": anime_id},
        )
        media = result.get("Media")
        if not isinstance(media, dict):
            raise MetadataError(f"Anime {anime_id} was not found.")

        titles = media.get("title") or {}
        tags = media.get("tags") or []
        return AnimeDetails(
            anilist_id=int(media["id"]),
            title=self._title(titles),
            native_title=titles.get("native"),
            description=media.get("description"),
            status=media.get("status"),
            episodes=media.get("episodes"),
            score=(
                float(media["averageScore"])
                if media.get("averageScore") is not None
                else None
            ),
            genres=tuple(str(value) for value in (media.get("genres") or [])),
            tags=tuple(
                str(tag.get("name"))
                for tag in tags
                if isinstance(tag, dict) and tag.get("name")
            ),
            season=media.get("season"),
            year=media.get("seasonYear"),
            format=media.get("format"),
            duration_minutes=media.get("duration"),
            cover_url=(media.get("coverImage") or {}).get("large"),
            site_url=media.get("siteUrl"),
            is_favorite=bool(media.get("isFavourite", False)),
        )

    async def episodes(self, anime_id: int) -> list[EpisodeItem]:
        """Return numbered episode placeholders from known episode count.

        AniList provides episode count and duration, but not a canonical
        playback URL. Playback sources are resolved through provider adapters.
        """
        details = await self.details(anime_id)
        if details.episodes is None:
            return []
        return [
            EpisodeItem(
                anime_id=anime_id,
                number=number,
                duration_minutes=details.duration_minutes,
            )
            for number in range(1, details.episodes + 1)
        ]

    @staticmethod
    def _title(titles: object) -> str:
        """Choose an English, Romaji, or native title."""
        if not isinstance(titles, dict):
            return "Unknown anime"
        return str(
            titles.get("english")
            or titles.get("romaji")
            or titles.get("native")
            or "Unknown anime"
        )
