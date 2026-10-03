"""SQLAlchemy 2 database bootstrap and session management."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ani_watch.storage.models import Base


def sqlite_path(url: str) -> Path | None:
    """Return the SQLite database path when the URL points to a file."""
    if not url.startswith("sqlite:///"):
        return None
    return Path(url.removeprefix("sqlite:///")).expanduser()


def _ensure_sqlite_parent(url: str) -> None:
    """Create the parent directory for a file-backed SQLite database."""
    path = sqlite_path(url)
    if path is None or path.name == ":memory:":
        return
    path.parent.mkdir(parents=True, exist_ok=True)


class Database:
    """Create an engine and manage SQLAlchemy sessions."""

    def __init__(self, url: str) -> None:
        _ensure_sqlite_parent(url)
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(
            url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        self._session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    def create_schema(self) -> None:
        """Create all current tables for a new installation."""
        self.engine.dispose()
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Yield a transactional session and rollback on failure."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        """Close pooled database connections."""
        self.engine.dispose()
