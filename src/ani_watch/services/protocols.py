"""Dependency-inversion contracts used by application services."""

from typing import Protocol, runtime_checkable

from ani_watch.domain.details import AnimeDetails
from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.models import AnimeRef


@runtime_checkable
class AnimeCatalog(Protocol):
    """Metadata contract used by application services."""

    async def search(self, query: str) -> list[AnimeRef]:
        """Return matching anime references."""

    async def details(self, anime_id: int) -> AnimeDetails:
        """Return full metadata."""


@runtime_checkable
class EpisodeSource(Protocol):
    """Episode source contract used by playback orchestration."""

    async def episodes(self, anime: AnimeRef) -> list[EpisodeItem]:
        """Return available episode source metadata."""

    async def resolve(self, anime: AnimeRef, episode_number: int) -> EpisodeItem:
        """Resolve a playable episode."""


@runtime_checkable
class Player(Protocol):
    """Minimal player contract exposed to application services."""

    def load(self, uri: str) -> None:
        """Load a media URI."""

    def play(self) -> None:
        """Start playback."""

    def pause(self) -> None:
        """Pause playback."""

    def stop(self) -> None:
        """Stop playback."""

    def seek(self, seconds: int) -> None:
        """Seek by absolute seconds."""

    def set_volume(self, volume: int) -> None:
        """Set volume as a percentage."""

    def position(self) -> int:
        """Return current playback position in seconds."""
