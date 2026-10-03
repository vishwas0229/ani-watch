"""AniList GraphQL client."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from ani_watch.domain.errors import MetadataError, RateLimitError

GRAPHQL_URL = "https://graphql.anilist.co"

SEARCH_QUERY = """
query ($search: String, $perPage: Int) {
  Page(perPage: $perPage) {
    media(search: $search, type: ANIME, sort: SEARCH_MATCH) {
      id
      title { romaji english native }
      format
      status
      episodes
      averageScore
      genres
    }
  }
}
"""

DETAILS_QUERY = """
query ($id: Int!) {
  Media(id: $id, type: ANIME) {
    id
    title { romaji english native }
    description(asHtml: false)
    format
    status
    episodes
    averageScore
    genres
    season
    seasonYear
    startDate { year month day }
  }
}
"""


class AniListClient:
    """Small async client around the public AniList GraphQL endpoint."""

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        *,
        timeout: float = 10.0,
        retries: int = 3,
        access_token: str | None = None,
    ) -> None:
        self._client = http_client
        self._timeout = timeout
        self._retries = max(0, retries)
        self._access_token = access_token

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute one GraphQL operation with retry and rate-limit handling."""
        owned = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            for attempt in range(self._retries + 1):
                try:
                    response = await client.post(
                        GRAPHQL_URL,
                        json={"query": query, "variables": dict(variables or {})},
                        headers=headers,
                    )
                except httpx.HTTPError as exc:
                    if attempt >= self._retries:
                        raise MetadataError(f"AniList request failed: {exc}") from exc
                    await asyncio.sleep(2**attempt)
                    continue

                if response.status_code == 429:
                    if attempt >= self._retries:
                        raise RateLimitError("AniList rate limit reached.")
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    await asyncio.sleep(delay)
                    continue

                if response.status_code >= 500:
                    if attempt >= self._retries:
                        raise MetadataError(f"AniList server error: HTTP {response.status_code}")
                    await asyncio.sleep(2**attempt)
                    continue

                if response.status_code >= 400:
                    raise MetadataError(f"AniList request rejected: HTTP {response.status_code}")

                payload = response.json()
                if payload.get("errors"):
                    message = payload["errors"][0].get("message", "GraphQL error")
                    raise MetadataError(message)
                data = payload.get("data")
                if not isinstance(data, dict):
                    raise MetadataError("AniList returned no GraphQL data.")
                return data

            raise MetadataError("AniList request exhausted all retries.")
        finally:
            if owned:
                await client.aclose()

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search public anime metadata."""
        cleaned = query.strip()
        if not cleaned:
            return []
        data = await self.request(SEARCH_QUERY, {"search": cleaned, "perPage": limit})
        page = data.get("Page") or {}
        media = page.get("media") or []
        return [item for item in media if isinstance(item, dict)]

    async def details(self, anime_id: int) -> dict[str, Any]:
        """Fetch one anime's metadata by AniList ID."""
        data = await self.request(DETAILS_QUERY, {"id": anime_id})
        media = data.get("Media")
        if not isinstance(media, dict):
            raise MetadataError(f"AniList anime {anime_id} was not found.")
        return media
