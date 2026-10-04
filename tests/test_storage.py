from datetime import UTC, datetime
from pathlib import Path

from ani_watch.domain.models import AnimeDetails, WatchHistoryEntry
from ani_watch.services.library import LibraryService
from ani_watch.storage.database import Database
from ani_watch.storage.repositories import (
    AnimeRepository,
    EpisodeRepository,
    FavoriteRepository,
    HistoryRepository,
    ProgressRepository,
)


def make_db(tmp_path: Path) -> Database:
    db = Database(f"sqlite:///{tmp_path / 'test.db'}")
    db.create_schema()
    return db


def test_sqlite_database_creates_missing_parent_directory(tmp_path: Path) -> None:
    database_path = tmp_path / "nested" / "data" / "ani-watch.db"

    db = Database(f"sqlite:///{database_path}")
    db.create_schema()

    assert database_path.parent.is_dir()
    assert database_path.is_file()
    db.dispose()


def test_anime_repository_upserts_and_reads(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    repo = AnimeRepository(db)
    details = AnimeDetails(
        anilist_id=1,
        title="Sample",
        native_title="サンプル",
        genres=("Drama", "Fantasy"),
        episodes=12,
    )

    repo.upsert(details)
    loaded = repo.get(1)

    assert loaded is not None
    assert loaded.title == "Sample"
    assert loaded.genres == ("Drama", "Fantasy")


def test_favorites_and_progress_persist(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    AnimeRepository(db).upsert(AnimeDetails(anilist_id=2, title="Sample"))

    favorites = FavoriteRepository(db)
    favorites.add(2)
    assert favorites.list() == [2]
    favorites.remove(2)
    assert favorites.list() == []

    progress = ProgressRepository(db)
    progress.save(2, 1, 500, 1000)
    record = progress.get(2, 1)
    assert record is not None
    assert record.position_seconds == 500
    assert record.completed is False


def test_history_records_watch_activity(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    AnimeRepository(db).upsert(AnimeDetails(anilist_id=3, title="History Anime"))

    HistoryRepository(db).record(
        WatchHistoryEntry(
            anime_id=3,
            anime_title="History Anime",
            episode_number=4,
            progress_seconds=1200,
            duration_seconds=1200,
        )
    )

    rows = HistoryRepository(db).list_recent()
    assert rows[0].anime_id == 3
    assert rows[0].episode_number == 4


def test_history_projection_includes_anime_and_episode_titles(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    AnimeRepository(db).upsert(AnimeDetails(anilist_id=4, title="Projection Anime"))
    EpisodeRepository(db).upsert(
        4,
        7,
        title="The Turning Point",
    )
    HistoryRepository(db).record(
        WatchHistoryEntry(
            anime_id=4,
            anime_title="Projection Anime",
            episode_number=7,
            watched_at=datetime(2026, 10, 3, 21, 30, tzinfo=UTC),
            progress_seconds=600,
            duration_seconds=1200,
        )
    )

    entry = HistoryRepository(db).list_recent_entries(1)[0]

    assert entry.anime_title == "Projection Anime"
    assert entry.episode_title == "The Turning Point"
    assert entry.episode_number == 7
    assert entry.progress_seconds == 600


def test_continue_watching_projection_includes_anime_title(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    AnimeRepository(db).upsert(AnimeDetails(anilist_id=5, title="Continue Anime"))

    progress = ProgressRepository(db)
    progress.save(5, 8, 300, 1200)

    item = progress.list_continue_watching(1)[0]

    assert item.anime_title == "Continue Anime"
    assert item.episode_number == 8
    assert item.position_seconds == 300
    assert item.duration_seconds == 1200


def test_completion_history_is_idempotent(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    AnimeRepository(db).upsert(AnimeDetails(anilist_id=6, title="Completed Anime"))

    service = LibraryService(db)
    service.save_progress(6, 1, 1200, 1200)
    service.save_progress(6, 1, 1200, 1200)

    rows = HistoryRepository(db).list_recent_entries()
    assert len(rows) == 1
    assert rows[0].anime_id == 6
    assert rows[0].episode_number == 1
