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
        """Return deterministic candidates, preferring exact titles then slugs."""
        slug = "".join(char if char.isalnum() else "-" for char in anime.title.lower()).strip("-")
        patterns = (
            (0, f"{anime.title} - {episode.number:02d}.*"),
            (1, f"{slug} - {episode.number:02d}.*"),
            (2, f"{slug}-{episode.number:02d}.*"),
        )

        matches: dict[Path, int] = {}
        for rank, pattern in patterns:
            try:
                for path in self.root.rglob(pattern):
                    try:
                        if not path.is_file():
                            continue
                    except OSError:
                        continue
                    matches[path] = min(rank, matches.get(path, rank))
            except OSError:
                continue

        return sorted(matches, key=lambda path: (matches[path], path.as_posix().casefold()))

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
