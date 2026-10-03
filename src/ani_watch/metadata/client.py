"""Async AniList GraphQL client with retry and rate-limit handling."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from ani_watch.domain.errors import MetadataError


class AniListClient:
    """Small typed wrapper around the AniList GraphQL endpoint."""

    def __init__(
        self,
        url: str = "https://graphql.anilist.co",
        access_token: str | None = None,
        timeout: float = 15.0,
        retries: int = 3,
    ) -> None:
        self.url = url
        self.access_token = access_token
        self.timeout = timeout
        self.retries = max(0, retries)

    async def execute(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL request with bounded retry behavior."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        payload: dict[str, Any] = {"query": query}
        if variables is not None:
            payload["variables"] = dict(variables)

        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.url,
                        json=payload,
                        headers=headers,
                    )
                if response.status_code == 429:
                    retry_after = self._retry_after(response)
                    if attempt < self.retries:
                        await asyncio.sleep(retry_after)
                        continue
                    raise MetadataError("AniList rate limit exceeded.")

                response.raise_for_status()
                body = response.json()
                errors = body.get("errors")
                if errors:
                    message = "; ".join(
                        str(error.get("message", "GraphQL error")) for error in errors
                    )
                    raise MetadataError(message)
                data = body.get("data")
                if not isinstance(data, dict):
                    raise MetadataError("AniList returned an invalid GraphQL response.")
                return data
            except httpx.TimeoutException as exc:
                if attempt >= self.retries:
                    raise MetadataError("AniList request timed out.") from exc
                await asyncio.sleep(2**attempt)
            except httpx.HTTPError as exc:
                if attempt >= self.retries:
                    raise MetadataError(f"AniList request failed: {exc}") from exc
                await asyncio.sleep(2**attempt)

        raise MetadataError("AniList request failed after retries.")

    @staticmethod
    def _retry_after(response: httpx.Response) -> float:
        """Parse Retry-After safely; fall back to a short delay."""
        value = response.headers.get("Retry-After", "5")
        try:
            return max(1.0, min(float(value), 60.0))
        except ValueError:
            return 5.0
