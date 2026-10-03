"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ani_watch.config.settings import DatabaseSettings


class Database:
    """Application database facade."""

    def __init__(self, settings: DatabaseSettings) -> None:
        self.engine = create_engine(settings.url, pool_pre_ping=True)
        self.session_factory = sessionmaker(
            self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    def session(self) -> Session:
        """Return a new database session."""
        return self.session_factory()

    def sessions(self) -> Iterator[Session]:
        """Yield a managed session and commit successful work."""
        session = self.session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_schema(self) -> None:
        """Create tables for first-run local development."""
        from ani_watch.storage.models import Base

        Base.metadata.create_all(self.engine)

    def dispose(self) -> None:
        """Release database resources."""
        self.engine.dispose()
