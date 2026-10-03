"""Domain model for episode-list presentation and playback handoff."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EpisodeItem:
    """Provider-neutral episode data consumed by the TUI."""

    number: int
    title: str | None = None
    duration_minutes: int | None = None
    watched: bool = False
    available: bool = True
