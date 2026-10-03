"""SQLAlchemy 2 ORM models for Ani-Watch."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all persistence models."""


class AnimeRecord(Base):
    __tablename__ = "anime"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anilist_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    native_title: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(50))
    episodes: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Float)
    genres: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str | None] = mapped_column(Text)
    site_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    episodes_rel: Mapped[list["EpisodeRecord"]] = relationship(
        back_populates="anime",
        cascade="all, delete-orphan",
    )


class EpisodeRecord(Base):
    __tablename__ = "episode"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anime_id: Mapped[int] = mapped_column(
        ForeignKey("anime.id", ondelete="CASCADE"),
        index=True,
    )
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(255))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    source_uri: Mapped[str | None] = mapped_column(Text)
    local_path: Mapped[str | None] = mapped_column(Text)
    watched: Mapped[bool] = mapped_column(Boolean, default=False)

    anime: Mapped["AnimeRecord"] = relationship(back_populates="episodes_rel")
    history: Mapped[list["WatchHistoryRecord"]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
    )


class WatchHistoryRecord(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey("anime.id", ondelete="CASCADE"))
    episode_id: Mapped[int] = mapped_column(ForeignKey("episode.id", ondelete="CASCADE"))
    progress_seconds: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    episode: Mapped["EpisodeRecord"] = relationship(back_populates="history")


class FavoriteRecord(Base):
    __tablename__ = "favorite"

    anime_id: Mapped[int] = mapped_column(
        ForeignKey("anime.id", ondelete="CASCADE"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SettingRecord(Base):
    __tablename__ = "setting"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
