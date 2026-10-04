"""Configurable direct-media online provider.

The provider accepts a user-configured URL template that points directly to
authorized media such as an HLS playlist or MP4 file.
"""

from __future__ import annotations

from string import Formatter
from urllib.parse import quote, urlparse

from ani_watch.domain.errors import ProviderError
from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.contracts import MediaCandidate


class DirectUrlProvider:
    """Resolve user-configured direct media URLs for online playback."""

    name = "online"
    _allowed_fields = frozenset(
        {
            "anime_id",
            "episode",
            "episode_padded",
            "quality",
            "title",
        }
    )
    _allowed_schemes = frozenset({"http", "https", "file"})

    def __init__(self, template: str) -> None:
        self.template = template.strip()
        if not self.template:
            raise ValueError("Online media URL template cannot be empty.")
        self._validate_template()

    def _validate_template(self) -> None:
        for _, field_name, _, _ in Formatter().parse(self.template):
            if field_name is None:
                continue
            root = field_name.split(".", 1)[0].split("[", 1)[0]
            if root not in self._allowed_fields:
                allowed = ", ".join(sorted(self._allowed_fields))
                raise ValueError(
                    f"Unsupported online URL placeholder '{field_name}'. Use only: {allowed}."
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
            raise ProviderError("The online media URL template could not be rendered.") from exc

        parsed = urlparse(uri)
        if parsed.scheme not in self._allowed_schemes:
            raise ProviderError("Online media URL must use http, https, or file scheme.")
        if parsed.scheme in {"http", "https"} and not parsed.netloc:
            raise ProviderError("Online media URL must contain a valid host.")
        if parsed.scheme == "file" and not parsed.path:
            raise ProviderError("Online file URL must contain a path.")
        return uri

    async def available(self, anime: AnimeRef, episode: EpisodeRef) -> bool:
        try:
            self._render(anime, episode, "auto")
        except ProviderError:
            return False
        return True

    async def resolve(
        self,
        anime: AnimeRef,
        episode: EpisodeRef,
        *,
        quality: str | None = None,
    ) -> MediaCandidate | None:
        return MediaCandidate(
            uri=self._render(anime, episode, quality),
            provider=self.name,
            quality=quality,
        )
