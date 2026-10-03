from pathlib import Path

from sqlalchemy import inspect, text

from ani_watch.storage.database import Database
from ani_watch.storage.migrations import upgrade


def test_alembic_upgrade_creates_canonical_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "fresh" / "ani-watch.db"
    db = Database(f"sqlite:///{database_path}")

    upgrade(db.engine)

    tables = set(inspect(db.engine).get_table_names())
    assert {"anime", "episode", "favorite", "watch_history", "progress", "settings"} <= tables
    assert "alembic_version" in tables
    assert "schema_version" not in tables

    with db.engine.connect() as connection:
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    assert revision == "0001_initial"


def test_database_create_schema_delegates_to_alembic(tmp_path: Path) -> None:
    db = Database(f"sqlite:///{tmp_path / 'ani-watch.db'}")

    db.create_schema()

    tables = set(inspect(db.engine).get_table_names())
    assert "alembic_version" in tables
    assert "anime" in tables


def test_alembic_upgrade_is_idempotent(tmp_path: Path) -> None:
    db = Database(f"sqlite:///{tmp_path / 'ani-watch.db'}")

    upgrade(db.engine)
    upgrade(db.engine)

    with db.engine.connect() as connection:
        revisions = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalars().all()
    assert revisions == ["0001_initial"]
