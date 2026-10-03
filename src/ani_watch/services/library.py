"""Library and watch-tracking services."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, func, select

from ani_watch.domain.models import WatchHistoryEntry
from ani_watch.storage.database import Database
from ani_watch.storage.models import FavoriteRecord, HistoryRecord, ProgressRecord
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

        if completed:
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

    def continue_watching(self, limit: int = 20) -> list[ProgressRecord]:
        with self.db.session() as session:
            return list(
                session.scalars(
                    select(ProgressRecord)
                    .where(ProgressRecord.completed.is_(False))
                    .order_by(desc(ProgressRecord.updated_at))
                    .limit(limit)
                ).all()
            )

    def recently_watched(self, limit: int = 20) -> list[HistoryRecord]:
        return self.history.list_recent(limit)

    def statistics(self) -> dict[str, int]:
        with self.db.session() as session:
            watched = session.scalar(select(func.count(HistoryRecord.id))) or 0
            favorites = session.scalar(select(func.count()).select_from(FavoriteRecord)) or 0
        return {
            "watched_episodes": int(watched),
            "favorites": int(favorites),
        }
