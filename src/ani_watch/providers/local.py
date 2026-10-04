"""Local media provider for user-owned anime files."""

from __future__ import annotations

import re
from pathlib import Path

from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.contracts import MediaCandidate


class LocalFileProvider:
    """Resolve files from a user-configured local media directory."""

    name = "local"

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()

    @staticmethod
    def _slug(value: str) -> str:
        """Normalize a title so punctuation and whitespace become one separator."""
        return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")

    def _patterns(self, anime: AnimeRef, episode: EpisodeRef) -> tuple[tuple[int, str], ...]:
        """Return supported filename patterns in deterministic preference order."""
        number = episode.number
        padded = f"{number:02d}"
        title = anime.title.strip()
        slug = self._slug(title)
        return (
            (0, f"{title} - {padded}.*"),
            (1, f"{title} - {number}.*"),
            (2, f"{title} Episode {padded}.*"),
            (3, f"{title} Episode {number}.*"),
            (4, f"{title} E{padded}.*"),
            (5, f"{title} E{number}.*"),
            (6, f"{slug} - {padded}.*"),
            (7, f"{slug} - {number}.*"),
            (8, f"{slug} Episode {padded}.*"),
            (9, f"{slug} Episode {number}.*"),
            (10, f"{slug} E{padded}.*"),
            (11, f"{slug} E{number}.*"),
            (12, f"{slug}-{padded}.*"),
            (13, f"{slug}-{number}.*"),
            (14, f"{slug} {padded}.*"),
            (15, f"{slug} {number}.*"),
            (16, f"{slug}{padded}.*"),
            (17, f"{slug}{number}.*"),
        )

    def _folder_names(self, anime: AnimeRef) -> tuple[str, ...]:
        """Return common exact and normalized folder names for media libraries."""
        spaced = re.sub(r"[^a-zA-Z0-9]+", " ", anime.title).strip()
        return tuple(
            name
            for name in dict.fromkeys(
                (
                    anime.title.strip(),
                    spaced,
                    self._slug(anime.title),
                )
            )
            if name
        )

    def _candidates(self, anime: AnimeRef, episode: EpisodeRef) -> list[Path]:
        """Return deterministic candidates across common local media naming layouts."""
        matches: dict[Path, int] = {}

        for rank, pattern in self._patterns(anime, episode):
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

        # Also support libraries that store each anime in its own folder, e.g.
        # "Naruto Shippuden/Episode 01.mkv".
        episode_number = episode.number
        episode_patterns = (
            (20, f"Episode {episode_number:02d}.*"),
            (21, f"Episode {episode_number}.*"),
            (22, f"E{episode_number:02d}.*"),
            (23, f"E{episode_number}.*"),
            (24, f"{episode_number:02d}.*"),
            (25, f"{episode_number}.*"),
        )
        try:
            folder_roots = tuple(self.root / folder_name for folder_name in self._folder_names(anime))
        except (TypeError, AttributeError):
            folder_roots = ()

        for folder in folder_roots:
            try:
                if not folder.is_dir():
                    continue
                    for rank, pattern in episode_patterns:
                        for path in folder.rglob(pattern):
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
