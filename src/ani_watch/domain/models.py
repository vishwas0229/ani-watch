"""Small, dependency-light domain value objects."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnimeRef:
    """Stable identifier for an anime across adapters."""

    anilist_id: int
    title: str


@dataclass(frozen=True, slots=True)
class EpisodeRef:
    """Stable identifier for an episode within an anime."""

    anime_id: int
    number: int
