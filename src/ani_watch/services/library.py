"""Library and watch-tracking services."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, func, select

from ani_watch.domain.models import (
    ContinueWatchingItem,
    FavoriteAnime,
    RecentlyWatchedItem,
    WatchHistoryEntry,
)
from ani_watch.storage.database import Database
from ani_watch.storage.models import FavoriteRecord, HistoryRecord
from ani_watch.storage.repositories import (
    AnimeRepository,
    FavoriteRepository,
    HistoryRepository,
    ProgressRepository,
)


class LibraryService:
    """Coordinate favorites, progress, continue-watching and statistics."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.anime = AnimeRepository(db)
        self.favorites = FavoriteRepository(db)
        self.history = HistoryRepository(db)
        self.progress = ProgressRepository(db)

    def favorite(self, anime_id: int) -> None:
        self.favorites.add(anime_id)

    def unfavorite(self, anime_id: int) -> None:
        self.favorites.remove(anime_id)

    def favorite_entries(self, limit: int = 100) -> list[FavoriteAnime]:
        """Return persisted favorites with their stored anime metadata."""
        import json

        from ani_watch.storage.models import AnimeRecord

        with self.db.session() as session:
            rows = session.execute(
                select(
                    FavoriteRecord.anime_id,
                    AnimeRecord.title,
                    AnimeRecord.native_title,
                    AnimeRecord.status,
                    AnimeRecord.episodes,
                    AnimeRecord.score,
                    AnimeRecord.genres,
                )
                .join(AnimeRecord, AnimeRecord.id == FavoriteRecord.anime_id)
                .order_by(desc(FavoriteRecord.created_at), FavoriteRecord.anime_id)
                .limit(max(1, limit))
            ).all()

        favorites = []
        for anime_id, title, native_title, status, episodes, score, genres_json in rows:
            try:
                genres = tuple(json.loads(genres_json or "[]"))
            except json.JSONDecodeError:
                genres = ()
            favorites.append(
                FavoriteAnime(
                    anime_id=anime_id,
                    title=title,
                    native_title=native_title,
                    status=status,
                    episodes=episodes,
                    score=score,
                    genres=genres,
                )
            )
        return favorites

    def save_progress(
        self,
        anime_id: int,
        episode_number: int,
        position_seconds: int,
        duration_seconds: int | None,
    ) -> None:
        completed = (
            duration_seconds is not None
            and duration_seconds > 0
            and position_seconds >= duration_seconds * 0.9
        )
        self.progress.save(
            anime_id,
            episode_number,
            position_seconds,
            duration_seconds,
            completed=completed,
        )

        if completed and not self.history.has_recent_completion(anime_id, episode_number):
            details = self.anime.get(anime_id)
            self.history.record(
                WatchHistoryEntry(
                    anime_id=anime_id,
                    anime_title=details.title if details else "Unknown anime",
                    episode_number=episode_number,
                    watched_at=datetime.now(UTC),
                    progress_seconds=position_seconds,
                    duration_seconds=duration_seconds,
                )
            )

    def continue_watching(self, limit: int = 20) -> list[ContinueWatchingItem]:
        return self.progress.list_continue_watching(limit)

    def recently_watched(self, limit: int = 20) -> list[WatchHistoryEntry]:
        return self.history.list_recent_entries(limit)

    def recently_completed(self, limit: int = 20) -> list[RecentlyWatchedItem]:
        return [
            RecentlyWatchedItem(
                anime_id=entry.anime_id,
                anime_title=entry.anime_title,
                episode_number=entry.episode_number,
            )
            for entry in self.recently_watched(limit)
        ]

    def statistics(self) -> dict[str, int]:
        with self.db.session() as session:
            watched = session.scalar(select(func.count(HistoryRecord.id))) or 0
            favorites = session.scalar(select(func.count()).select_from(FavoriteRecord)) or 0
        return {
            "watched_episodes": int(watched),
            "favorites": int(favorites),
        }
