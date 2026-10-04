"""Streamlink-backed online provider.

The provider accepts a user-configured streaming page or direct stream URL,
lets Streamlink resolve supported services/protocols, and returns a playable
HTTP/HLS URL for the existing VLC pipeline.
"""

from __future__ import annotations

import asyncio
import re
from string import Formatter
from urllib.parse import quote, urlparse

from ani_watch.domain.errors import ProviderError
from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.contracts import MediaCandidate

try:
    import streamlink
except ImportError:  # pragma: no cover - dependency is installed by project metadata
    streamlink = None


class StreamlinkProvider:
    """Resolve supported streaming URLs through Streamlink."""

    name = "streamlink"
    _allowed_fields = frozenset(
        {
            "anime_id",
            "episode",
            "episode_padded",
            "quality",
            "title",
        }
    )
    _allowed_schemes = frozenset({"http", "https"})

    def __init__(self, template: str) -> None:
        self.template = template.strip()
        if not self.template:
            raise ValueError("Streamlink URL template cannot be empty.")
        self._validate_template()

    def _validate_template(self) -> None:
        for _, field_name, _, _ in Formatter().parse(self.template):
            if field_name is None:
                continue
            root = field_name.split(".", 1)[0].split("[", 1)[0]
            if root not in self._allowed_fields:
                allowed = ", ".join(sorted(self._allowed_fields))
                raise ValueError(
                    f"Unsupported Streamlink URL placeholder '{field_name}'. "
                    f"Use only: {allowed}."
                )

    def _render(self, anime: AnimeRef, episode: EpisodeRef, quality: str | None) -> str:
        try:
            uri = self.template.format(
                anime_id=anime.anilist_id,
                episode=episode.number,
                episode_padded=f"{episode.number:02d}",
                quality=quality or "auto",
                title=quote(anime.title, safe=""),
            ).strip()
        except (KeyError, ValueError) as exc:
            raise ProviderError(
                "The Streamlink URL template could not be rendered."
            ) from exc

        parsed = urlparse(uri)
        if parsed.scheme not in self._allowed_schemes:
            raise ProviderError("Streamlink URL must use http or https scheme.")
        if not parsed.netloc:
            raise ProviderError("Streamlink URL must contain a valid host.")
        return uri

    @staticmethod
    def _pick_stream(streams, quality: str | None):
        if not streams:
            return None, None

        if quality in {None, "auto"}:
            return "best", streams.get("best")

        requested = quality.lower()
        exact = streams.get(requested)
        if exact is not None:
            return requested, exact

        prefixed = [
            (name, stream)
            for name, stream in streams.items()
            if str(name).lower().startswith(requested)
        ]
        if prefixed:
            return sorted(prefixed, key=lambda item: str(item[0]))[0]

        return "best", streams.get("best")

    async def available(self, anime: AnimeRef, episode: EpisodeRef) -> bool:
        """Return whether the configured Streamlink URL can be rendered."""
        try:
            self._render(anime, episode, "auto")
        except ProviderError:
            return False
        return streamlink is not None

    async def resolve(
        self,
        anime: AnimeRef,
        episode: EpisodeRef,
        *,
        quality: str | None = None,
    ) -> MediaCandidate | None:
        """Resolve a supported streaming page into a VLC-playable URL."""
        if streamlink is None:
            raise ProviderError(
                "Streamlink is not installed. Reinstall Ani-Watch with its current dependencies."
            )

        source_url = self._render(anime, episode, quality)
        try:
            streams = await asyncio.to_thread(streamlink.streams, source_url)
        except Exception as exc:
            raise ProviderError(
                f"Streamlink could not resolve the configured URL: {exc}"
            ) from exc

        selected_name, selected = self._pick_stream(streams, quality)
        if selected is None:
            raise ProviderError(
                "Streamlink found no playable streams for the configured URL."
            )

        playable_url = getattr(selected, "url", None)
        if not isinstance(playable_url, str) or not playable_url:
            raise ProviderError(
                "Streamlink returned a stream type that cannot be passed directly to VLC. "
                "Use a direct HLS/HTTP media URL or another supported Streamlink stream."
            )

        return MediaCandidate(
            uri=playable_url,
            provider=self.name,
            quality=selected_name,
        )
