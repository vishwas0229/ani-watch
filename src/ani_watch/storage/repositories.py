"""Persistence repositories for library and tracking data."""

from __future__ import annotations

import json
from datetime import datetime
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ani_watch.domain.details import AnimeDetails
from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.favorite import FavoriteAnime
from ani_watch.domain.history import WatchHistoryEntry
from .models import AnimeRecord, EpisodeRecord, FavoriteRecord, SettingRecord, WatchHistoryRecord


class AnimeRepository:
    """Store and retrieve anime metadata."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, anime: AnimeDetails) -> AnimeRecord:
        record = self.session.scalar(
            select(AnimeRecord).where(AnimeRecord.anilist_id == anime.anilist_id)
        )
        if record is None:
            record = AnimeRecord(anilist_id=anime.anilist_id, title=anime.title)
            self.session.add(record)
        record.title = anime.title
        record.native_title = anime.native_title
        record.status = anime.status
        record.episodes = anime.episodes
        record.score = anime.score
        record.genres = json.dumps(list(anime.genres))
        record.cover_url = anime.cover_url
        record.site_url = anime.site_url
        self.session.flush()
        return record

    def get_by_anilist_id(self, anime_id: int) -> AnimeRecord | None:
        return self.session.scalar(
            select(AnimeRecord).where(AnimeRecord.anilist_id == anime_id)
        )


class EpisodeRepository:
    """Store and retrieve episode metadata."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, anime_record: AnimeRecord, episode: EpisodeItem) -> EpisodeRecord:
        record = self.session.scalar(
            select(EpisodeRecord).where(
                EpisodeRecord.anime_id == anime_record.id,
                EpisodeRecord.number == episode.number,
            )
        )
        if record is None:
            record = EpisodeRecord(
                anime_id=anime_record.id,
                number=episode.number,
            )
            self.session.add(record)
        record.title = episode.title
        record.duration_seconds = (
            episode.duration_minutes * 60
            if episode.duration_minutes is not None
            else None
        )
        record.source_uri = episode.source_uri
        record.local_path = episode.local_path
        record.watched = episode.watched
        self.session.flush()
        return record

    def list_for_anime(self, anime_id: int) -> list[EpisodeRecord]:
        return list(
            self.session.scalars(
                select(EpisodeRecord)
                .join(AnimeRecord)
                .where(AnimeRecord.anilist_id == anime_id)
                .order_by(EpisodeRecord.number)
            )
        )


class FavoritesRepository:
    """Persist user favorites."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, anime_id: int) -> None:
        self.session.merge(FavoriteRecord(anime_id=anime_id))

    def remove(self, anime_id: int) -> None:
        record = self.session.get(FavoriteRecord, anime_id)
        if record:
            self.session.delete(record)

    def contains(self, anime_id: int) -> bool:
        return self.session.get(FavoriteRecord, anime_id) is not None

    def list(self) -> list[FavoriteAnime]:
        statement = (
            select(AnimeRecord)
            .join(FavoriteRecord, FavoriteRecord.anime_id == AnimeRecord.id)
            .order_by(desc(FavoriteRecord.added_at))
        )
        return [
            FavoriteAnime(
                anime_id=record.anilist_id,
                title=record.title,
                native_title=record.native_title,
                status=record.status,
                episodes=record.episodes,
                score=record.score,
                genres=tuple(json.loads(record.genres or "[]")),
                cover_url=record.cover_url,
            )
            for record in self.session.scalars(statement)
        ]


class WatchHistoryRepository:
    """Persist playback position and watched history."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_progress(
        self,
        anime_id: int,
        episode_id: int,
        progress_seconds: int,
        duration_seconds: int | None,
        watched: bool,
    ) -> None:
        record = self.session.scalar(
            select(WatchHistoryRecord)
            .where(
                WatchHistoryRecord.episode_id == episode_id,
            )
            .order_by(desc(WatchHistoryRecord.watched_at))
        )
        if record is None:
            record = WatchHistoryRecord(
                anime_id=anime_id,
                episode_id=episode_id,
            )
            self.session.add(record)
        record.progress_seconds = max(0, progress_seconds)
        record.duration_seconds = duration_seconds
        record.watched_at = datetime.utcnow()
        episode = self.session.get(EpisodeRecord, episode_id)
        if episode is not None:
            episode.watched = watched

    def recent(self, limit: int = 25) -> list[WatchHistoryEntry]:
        statement = (
            select(WatchHistoryRecord, EpisodeRecord, AnimeRecord)
            .join(EpisodeRecord, EpisodeRecord.id == WatchHistoryRecord.episode_id)
            .join(AnimeRecord, AnimeRecord.id == WatchHistoryRecord.anime_id)
            .order_by(desc(WatchHistoryRecord.watched_at))
            .limit(limit)
        )
        entries: list[WatchHistoryEntry] = []
        for record, episode, anime in self.session.execute(statement):
            entries.append(
                WatchHistoryEntry(
                    anime_id=anime.anilist_id,
                    anime_title=anime.title,
                    episode_number=episode.number,
                    episode_title=episode.title,
                    watched_at=record.watched_at,
                    progress_seconds=record.progress_seconds,
                    duration_seconds=record.duration_seconds,
                )
            )
        return entries


class SettingsRepository:
    """Persist individual setting values."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def set(self, key: str, value: str) -> None:
        self.session.merge(SettingRecord(key=key, value=value))

    def get(self, key: str) -> str | None:
        record = self.session.get(SettingRecord, key)
        return record.value if record else None
