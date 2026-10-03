"""Conflict-aware synchronization helpers."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SyncConflict:
    """Represent differing local and remote tracking state."""

    media_id: int
    local_progress: int
    remote_progress: int
    local_status: str | None
    remote_status: str | None


def resolve_progress_conflict(
    conflict: SyncConflict,
    strategy: str = "remote",
) -> int:
    """Resolve a progress conflict using an explicit deterministic policy."""
    if strategy == "local":
        return conflict.local_progress
    if strategy == "max":
        return max(conflict.local_progress, conflict.remote_progress)
    return conflict.remote_progress
