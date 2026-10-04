"""Repository implementations for library, progress and settings."""

import json
from datetime import UTC, datetime

from sqlalchemy import delete, desc, select

from ani_watch.domain.models import (
    AnimeDetails,
    ContinueWatchingItem,
    WatchHistoryEntry,
)
from ani_watch.storage.database import Database
from ani_watch.storage.models import (
    AnimeRecord,
    EpisodeRecord,
    FavoriteRecord,
    HistoryRecord,
    ProgressRecord,
    SettingsRecord,
)


class AnimeRepository:
    """CRUD operations for anime metadata."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def upsert(self, details: AnimeDetails) -> None:
        with self.db.session() as session:
            record = session.get(AnimeRecord, details.anilist_id)
            if record is None:
                record = AnimeRecord(id=details.anilist_id)
                session.add(record)

            record.title = details.title
            record.native_title = details.native_title
            record.description = details.description
            record.status = details.status
            record.episodes = details.episodes
            record.score = details.score
            record.genres = json.dumps(details.genres)
            record.season = details.season
            record.year = details.year
            record.format = details.format
            record.updated_at = datetime.now(UTC)

    def get(self, anime_id: int) -> AnimeDetails | None:
        with self.db.session() as session:
            record = session.get(AnimeRecord, anime_id)
            if record is None:
                return None

            try:
                genres = tuple(json.loads(record.genres or "[]"))
            except json.JSONDecodeError:
                genres = ()

            return AnimeDetails(
                anilist_id=record.id,
                title=record.title,
                native_title=record.native_title,
                description=record.description,
                status=record.status,
                episodes=record.episodes,
                score=record.score,
                genres=genres,
                season=record.season,
                year=record.year,
                format=record.format,
                is_favorite=session.get(FavoriteRecord, record.id) is not None,
            )


class EpisodeRepository:
    """CRUD operations for episode metadata and media handoff."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def upsert(self, anime_id: int, number: int, **values) -> None:
        with self.db.session() as session:
            record = session.execute(
                select(EpisodeRecord).where(
                    EpisodeRecord.anime_id == anime_id,
                    EpisodeRecord.number == number,
                )
            ).scalar_one_or_none()

            if record is None:
                record = EpisodeRecord(
                    anime_id=anime_id,
                    number=number,
                )
                session.add(record)

            for key, value in values.items():
                if hasattr(record, key):
                    setattr(record, key, value)

    def get_media_uri(self, anime_id: int, number: int) -> str | None:
        with self.db.session() as session:
            record = session.execute(
                select(EpisodeRecord).where(
                    EpisodeRecord.anime_id == anime_id,
                    EpisodeRecord.number == number,
                )
            ).scalar_one_or_none()
            return record.media_uri if record else None


class FavoriteRepository:
    """Manage favorite anime records."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, anime_id: int) -> None:
        with self.db.session() as session:
            if session.get(FavoriteRecord, anime_id) is None:
                session.add(FavoriteRecord(anime_id=anime_id))

    def remove(self, anime_id: int) -> None:
        with self.db.session() as session:
            session.execute(delete(FavoriteRecord).where(FavoriteRecord.anime_id == anime_id))

    def list(self) -> list[int]:
        with self.db.session() as session:
            return list(session.scalars(select(FavoriteRecord.anime_id)).all())


class HistoryRepository:
    """Persist recent watch activity."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def record(self, entry: WatchHistoryEntry) -> None:
        with self.db.session() as session:
            session.add(
                HistoryRecord(
                    anime_id=entry.anime_id,
                    episode_number=entry.episode_number,
                    watched_at=entry.watched_at or datetime.now(UTC),
                    progress_seconds=max(0, entry.progress_seconds),
                    duration_seconds=entry.duration_seconds,
                )
            )

    def list_recent(self, limit: int = 50) -> list[HistoryRecord]:
        with self.db.session() as session:
            return list(
                session.scalars(
                    select(HistoryRecord).order_by(desc(HistoryRecord.watched_at)).limit(limit)
                ).all()
            )

    def list_recent_entries(self, limit: int = 50) -> list[WatchHistoryEntry]:
        """Return history rows projected into the provider-neutral domain model."""
        with self.db.session() as session:
            rows = session.execute(
                select(
                    HistoryRecord,
                    AnimeRecord.title,
                    EpisodeRecord.title,
                )
                .outerjoin(AnimeRecord, AnimeRecord.id == HistoryRecord.anime_id)
                .outerjoin(
                    EpisodeRecord,
                    (EpisodeRecord.anime_id == HistoryRecord.anime_id)
                    & (EpisodeRecord.number == HistoryRecord.episode_number),
                )
                .order_by(desc(HistoryRecord.watched_at), desc(HistoryRecord.id))
                .limit(max(1, limit))
            ).all()

        return [
            WatchHistoryEntry(
                anime_id=record.anime_id,
                anime_title=anime_title or "Unknown anime",
                episode_number=record.episode_number,
                episode_title=episode_title,
                watched_at=record.watched_at,
                progress_seconds=record.progress_seconds,
                duration_seconds=record.duration_seconds,
            )
            for record, anime_title, episode_title in rows
        ]

    def has_recent_completion(self, anime_id: int, episode_number: int) -> bool:
        """Return whether this episode already has a recorded completion."""
        with self.db.session() as session:
            return (
                session.scalar(
                    select(HistoryRecord.id)
                    .where(
                        HistoryRecord.anime_id == anime_id,
                        HistoryRecord.episode_number == episode_number,
                        HistoryRecord.duration_seconds.is_not(None),
                        HistoryRecord.progress_seconds >= HistoryRecord.duration_seconds * 0.9,
                    )
                    .limit(1)
                )
                is not None
            )


class ProgressRepository:
    """Persist playback position and completion state."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save(
        self,
        anime_id: int,
        episode_number: int,
        position_seconds: int,
        duration_seconds: int | None,
        completed: bool = False,
    ) -> None:
        with self.db.session() as session:
            record = session.execute(
                select(ProgressRecord).where(
                    ProgressRecord.anime_id == anime_id,
                    ProgressRecord.episode_number == episode_number,
                )
            ).scalar_one_or_none()

            if record is None:
                record = ProgressRecord(
                    anime_id=anime_id,
                    episode_number=episode_number,
                )
                session.add(record)

            record.position_seconds = max(0, position_seconds)
            record.duration_seconds = duration_seconds
            record.completed = completed
            record.updated_at = datetime.now(UTC)

    def get(
        self,
        anime_id: int,
        episode_number: int,
    ) -> ProgressRecord | None:
        with self.db.session() as session:
            return session.execute(
                select(ProgressRecord).where(
                    ProgressRecord.anime_id == anime_id,
                    ProgressRecord.episode_number == episode_number,
                )
            ).scalar_one_or_none()

    def list_for_anime(self, anime_id: int) -> list[ProgressRecord]:
        """Return every tracked progress row for one anime."""
        with self.db.session() as session:
            return list(
                session.scalars(
                    select(ProgressRecord)
                    .where(ProgressRecord.anime_id == anime_id)
                    .order_by(ProgressRecord.episode_number)
                ).all()
            )

    def list_all(self, limit: int = 1000) -> list[ProgressRecord]:
        """Return tracked progress rows for local AniList sync."""
        with self.db.session() as session:
            return list(
                session.scalars(
                    select(ProgressRecord)
                    .order_by(desc(ProgressRecord.updated_at))
                    .limit(max(1, limit))
                ).all()
            )

    def list_continue_watching(self, limit: int = 20) -> list[ContinueWatchingItem]:
        """Return incomplete progress rows with anime titles in one projection query."""
        with self.db.session() as session:
            rows = session.execute(
                select(
                    ProgressRecord,
                    AnimeRecord.title,
                )
                .outerjoin(AnimeRecord, AnimeRecord.id == ProgressRecord.anime_id)
                .where(ProgressRecord.completed.is_(False))
                .order_by(desc(ProgressRecord.updated_at))
                .limit(max(1, limit))
            ).all()

        return [
            ContinueWatchingItem(
                anime_id=record.anime_id,
                anime_title=anime_title or "Unknown anime",
                episode_number=record.episode_number,
                position_seconds=record.position_seconds,
                duration_seconds=record.duration_seconds,
            )
            for record, anime_title in rows
        ]


class SettingsRepository:
    """Persist small application settings alongside the config file."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def set(self, key: str, value: str) -> None:
        with self.db.session() as session:
            record = session.get(SettingsRecord, key)
            if record is None:
                session.add(SettingsRecord(key=key, value=value))
            else:
                record.value = value
                record.updated_at = datetime.now(UTC)

    def get(self, key: str) -> str | None:
        with self.db.session() as session:
            record = session.get(SettingsRecord, key)
            return record.value if record else None
