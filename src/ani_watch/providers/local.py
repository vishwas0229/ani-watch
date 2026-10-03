"""Local media provider for user-owned anime files."""

from __future__ import annotations

from pathlib import Path

from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.contracts import MediaCandidate


class LocalFileProvider:
    """Resolve files from a user-configured local media directory."""

    name = "local"

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()

    def _candidates(self, anime: AnimeRef, episode: EpisodeRef) -> list[Path]:
        slug = "".join(char if char.isalnum() else "-" for char in anime.title.lower()).strip("-")
        patterns = (
            f"{slug}-{episode.number:02d}.*",
            f"{slug} - {episode.number:02d}.*",
            f"{anime.title} - {episode.number:02d}.*",
        )
        matches: list[Path] = []
        for pattern in patterns:
            matches.extend(self.root.rglob(pattern))
        return [path for path in matches if path.is_file()]

    async def available(self, anime: AnimeRef, episode: EpisodeRef) -> bool:
        return bool(self._candidates(anime, episode))

    async def resolve(
        self,
        anime: AnimeRef,
        episode: EpisodeRef,
        *,
        quality: str | None = None,
    ) -> MediaCandidate | None:
        candidates = self._candidates(anime, episode)
        if not candidates:
            return None
        return MediaCandidate(
            uri=candidates[0].as_uri(),
            provider=self.name,
            quality=quality,
        )
