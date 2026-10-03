"""Core provider-neutral domain models."""

from dataclasses import dataclass
from datetime import datetime


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


@dataclass(frozen=True, slots=True)
class AnimeDetails:
    """Metadata required to render one anime."""

    anilist_id: int
    title: str
    native_title: str | None = None
    description: str | None = None
    status: str | None = None
    episodes: int | None = None
    score: float | None = None
    genres: tuple[str, ...] = ()
    season: str | None = None
    year: int | None = None
    format: str | None = None
    is_favorite: bool = False


@dataclass(frozen=True, slots=True)
class EpisodeItem:
    """Provider-neutral episode data consumed by the TUI."""

    number: int
    title: str | None = None
    duration_minutes: int | None = None
    watched: bool = False
    available: bool = True


@dataclass(frozen=True, slots=True)
class WatchHistoryEntry:
    """Locally stored watch activity."""

    anime_id: int
    anime_title: str
    episode_number: int
    episode_title: str | None = None
    watched_at: datetime | None = None
    progress_seconds: int = 0
    duration_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class FavoriteAnime:
    """Saved anime favorite."""

    anime_id: int
    title: str
    native_title: str | None = None
    status: str | None = None
    episodes: int | None = None
    score: float | None = None
    genres: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ContinueWatchingItem:
    """A partially watched episode."""

    anime_id: int
    anime_title: str
    episode_number: int
    position_seconds: int
    duration_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class RecentlyWatchedItem:
    """A recently completed episode."""

    anime_id: int
    anime_title: str
    episode_number: int


@dataclass(frozen=True, slots=True)
class LibrarySnapshot:
    """Aggregated data rendered by the library dashboard."""

    continue_watching: tuple[ContinueWatchingItem, ...] = ()
    recently_watched: tuple[RecentlyWatchedItem, ...] = ()
    watched_episodes: int = 0
    favorites: int = 0
