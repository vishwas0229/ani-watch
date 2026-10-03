"""Local media provider for user-owned files."""

from __future__ import annotations

from pathlib import Path
import re

from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.models import AnimeRef
from .base import EpisodeProvider


class LocalProvider(EpisodeProvider):
    """Resolve local files from configured directories."""

    name = "local"
    extensions = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v"}

    def __init__(self, directories: list[str], **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.directories = tuple(Path(directory).expanduser() for directory in directories)

    async def episodes(self, anime: AnimeRef) -> list[EpisodeItem]:
        """Discover local episode files matching the anime title."""
        results: list[EpisodeItem] = []
        normalized = self._normalize(anime.title)

        for directory in self.directories:
            if not directory.exists():
                continue
            for path in directory.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in self.extensions:
                    continue
                if normalized not in self._normalize(path.stem):
                    continue
                number = self._extract_episode(path.stem)
                if number is not None:
                    results.append(
                        EpisodeItem(
                            anime_id=anime.anilist_id,
                            number=number,
                            local_path=str(path),
                            source_uri=path.resolve().as_uri(),
                        )
                    )
        return sorted(results, key=lambda item: item.number)

    async def resolve(self, anime: AnimeRef, episode_number: int) -> EpisodeItem:
        """Resolve one locally owned episode."""
        episodes = await self.episodes(anime)
        for episode in episodes:
            if episode.number == episode_number:
                return episode
        raise FileNotFoundError(
            f"Local episode {episode_number} for {anime.title!r} was not found."
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(character.lower() for character in value if character.isalnum())

    @staticmethod
    def _extract_episode(stem: str) -> int | None:
        match = re.search(r"(?:^|[\\s._-])(?:s\\d{1,2})?e(\\d{1,4})(?:$|[\\s._-])", stem, re.I)
        if match:
            return int(match.group(1))
        match = re.search(
            r"(?:^|[\\s._-])(?:ep(?:isode)?[\\s._-]*)?(\\d{1,4})(?:$|[\\s._-])",
            stem,
            re.I,
        )
        return int(match.group(1)) if match else None
