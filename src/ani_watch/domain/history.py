"""Domain model for locally stored watch-history entries."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class WatchHistoryEntry:
    """Provider-neutral record for one watched episode."""

    anime_id: int
    anime_title: str
    episode_number: int
    episode_title: str | None = None
    watched_at: datetime | None = None
    progress_seconds: int = 0
    duration_seconds: int | None = None
