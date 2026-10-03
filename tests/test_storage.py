from pathlib import Path

from ani_watch.domain.models import AnimeDetails, WatchHistoryEntry
from ani_watch.storage.database import Database
from ani_watch.storage.repositories import (
    AnimeRepository,
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
