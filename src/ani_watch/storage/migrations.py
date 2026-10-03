"""Alembic-backed database migration helpers."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine

from ani_watch.domain.errors import StorageError

MIGRATION_HEAD = "head"


def _project_root() -> Path:
    """Return the repository/package root containing Alembic configuration."""
    return Path(__file__).resolve().parents[3]


def _alembic_config(engine: Engine) -> Config:
    """Build an Alembic config for the configured database engine."""
    root = _project_root()
    ini_path = root / "alembic.ini"
    migrations_dir = root / "migrations"

    if not ini_path.is_file() or not migrations_dir.is_dir():
        raise StorageError(
            "Alembic migration files are unavailable. Reinstall Ani-Watch "
            "with the complete distribution."
        )

    config = Config(str(ini_path))
    config.set_main_option("script_location", str(migrations_dir))
    database_url = engine.url.render_as_string(hide_password=False).replace("%", "%%")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade(engine: Engine) -> None:
    """Upgrade the database to the latest Alembic revision."""
    command.upgrade(_alembic_config(engine), MIGRATION_HEAD)
