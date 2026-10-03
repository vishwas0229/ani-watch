"""Dependency-inversion contracts used by application services."""

from typing import Protocol

from ani_watch.domain.models import AnimeRef, EpisodeRef


class AnimeCatalog(Protocol):
    """Metadata contract used by application services."""

    async def search(self, query: str) -> list[AnimeRef]:
        """Return matching anime references."""


class EpisodeSource(Protocol):
    """Episode lookup contract for playback orchestration."""

    async def episodes(self, anime: AnimeRef) -> list[EpisodeRef]:
        """Return available episodes for an anime."""
