"""Application service for library, history, progress, and statistics."""

from __future__ import annotations

from dataclasses import dataclass

from ani_watch.domain.details import AnimeDetails
from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.favorite import FavoriteAnime
from ani_watch.domain.history import WatchHistoryEntry

from .db import Database
from .models import AnimeRecord
from .repositories import AnimeRepository, EpisodeRepository, FavoritesRepository, WatchHistoryRepository


@dataclass(frozen=True, slots=True)
class LibraryStatistics:
    favorite_count: int
    watched_episodes: int
    total_watch_seconds: int


class LibraryService:
    """Coordinate local library operations."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def save_anime_and_episodes(
        self,
        anime: AnimeDetails,
        episodes: list[EpisodeItem],
    ) -> None:
        with self.database.session() as session:
            anime_repo = AnimeRepository(session)
            episode_repo = EpisodeRepository(session)
            record = anime_repo.upsert(anime)
            for episode in episodes:
                episode_repo.upsert(record, episode)
            session.commit()

    def set_favorite(self, anime: AnimeDetails, favorite: bool) -> None:
        with self.database.session() as session:
            anime_repo = AnimeRepository(session)
            record = anime_repo.upsert(anime)
            favorites = FavoritesRepository(session)
            if favorite:
                favorites.add(record.id)
            else:
                favorites.remove(record.id)
            session.commit()

    def favorites(self) -> list[FavoriteAnime]:
        with self.database.session() as session:
            return FavoritesRepository(session).list()

    def history(self, limit: int = 25) -> list[WatchHistoryEntry]:
        with self.database.session() as session:
            return WatchHistoryRepository(session).recent(limit)

    def record_progress(
        self,
        anime: AnimeDetails,
        episode_number: int,
        progress_seconds: int,
        duration_seconds: int | None,
    ) -> None:
        with self.database.session() as session:
            anime_record = AnimeRepository(session).upsert(anime)
            episode = EpisodeRepository(session).upsert(
                anime_record,
                EpisodeItem(
                    anime_id=anime.anilist_id,
                    number=episode_number,
                    duration_minutes=(
                        duration_seconds // 60 if duration_seconds else None
                    ),
                ),
            )
            WatchHistoryRepository(session).upsert_progress(
                anime_id=anime_record.id,
                episode_id=episode.id,
                progress_seconds=progress_seconds,
                duration_seconds=duration_seconds,
                watched=(
                    duration_seconds is not None
                    and duration_seconds > 0
                    and progress_seconds >= duration_seconds * 0.9
                ),
            )
            session.commit()

    def statistics(self) -> LibraryStatistics:
        with self.database.session() as session:
            rows = WatchHistoryRepository(session).recent(1000)
            return LibraryStatistics(
                favorite_count=len(FavoritesRepository(session).list()),
                watched_episodes=sum(
                    1
                    for entry in rows
                    if entry.duration_seconds
                    and entry.progress_seconds >= entry.duration_seconds * 0.9
                ),
                total_watch_seconds=sum(entry.progress_seconds for entry in rows),
            )

    def recently_watched(self, limit: int = 10) -> list[WatchHistoryEntry]:
        return self.history(limit)
