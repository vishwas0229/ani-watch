"""View models for the library dashboard."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContinueWatchingItem:
    anime_id: int
    anime_title: str
    episode_number: int
    position_seconds: int
    duration_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class RecentlyWatchedItem:
    anime_id: int
    anime_title: str
    episode_number: int


@dataclass(frozen=True, slots=True)
class LibrarySnapshot:
    continue_watching: tuple[ContinueWatchingItem, ...] = ()
    recently_watched: tuple[RecentlyWatchedItem, ...] = ()
    watched_episodes: int = 0
    favorites: int = 0
