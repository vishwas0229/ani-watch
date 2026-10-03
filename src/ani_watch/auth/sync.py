"""Authenticated AniList list synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ani_watch.domain.errors import MetadataError
from ani_watch.metadata.client import AniListClient


@dataclass(frozen=True, slots=True)
class AniListListEntry:
    """Subset of a user's AniList entry used by Ani-Watch."""

    media_id: int
    title: str
    status: str | None
    progress: int
    score: float


class AniListSyncService:
    """Pull and push the user's AniList anime list."""

    def __init__(self, client: AniListClient) -> None:
        self.client = client

    async def viewer_id(self) -> int:
        """Return the authenticated user's ID."""
        data = await self.client.execute("{ Viewer { id } }")
        viewer = data.get("Viewer")
        if not isinstance(viewer, dict) or viewer.get("id") is None:
            raise MetadataError("AniList authentication is invalid.")
        return int(viewer["id"])

    async def pull_watch_list(self) -> list[AniListListEntry]:
        """Pull the full anime list grouped by status."""
        user_id = await self.viewer_id()
        data = await self.client.execute(
            """
            query WatchList($userId: Int) {
              MediaListCollection(userId: $userId, type: ANIME) {
                lists {
                  entries {
                    mediaId
                    status
                    progress
                    score
                    media { id title { english romaji native } }
                  }
                }
              }
            }
            """,
            {"userId": user_id},
        )
        collection = data.get("MediaListCollection") or {}
        output: list[AniListListEntry] = []
        for group in collection.get("lists", []):
            for entry in group.get("entries", []):
                media = entry.get("media") or {}
                title_data = media.get("title") or {}
                title = (
                    title_data.get("english")
                    or title_data.get("romaji")
                    or title_data.get("native")
                    or "Unknown anime"
                )
                output.append(
                    AniListListEntry(
                        media_id=int(entry["mediaId"]),
                        title=str(title),
                        status=entry.get("status"),
                        progress=int(entry.get("progress") or 0),
                        score=float(entry.get("score") or 0),
                    )
                )
        return output

    async def push_progress(self, media_id: int, progress: int) -> dict[str, Any]:
        """Push episode progress."""
        return await self._save_entry(media_id, progress=progress)

    async def update_status(self, media_id: int, status: str) -> dict[str, Any]:
        """Update AniList list status."""
        return await self._save_entry(media_id, status=status)

    async def update_score(self, media_id: int, score: float) -> dict[str, Any]:
        """Update AniList score."""
        return await self._save_entry(media_id, score=score)

    async def _save_entry(self, media_id: int, **values: object) -> dict[str, Any]:
        """Save one AniList media-list entry."""
        arguments = ["$mediaId: Int!"]
        variables: dict[str, object] = {"mediaId": media_id}
        assignments: list[str] = []

        for key, value in values.items():
            if key == "status":
                arguments.append("$status: MediaListStatus")
            elif key == "progress":
                arguments.append("$progress: Int")
            elif key == "score":
                arguments.append("$score: Float")
            else:
                continue
            assignments.append(key + ": $" + key)
            variables[key] = value

        query = (
            "mutation SaveEntry("
            + ", ".join(arguments)
            + ") { SaveMediaListEntry(mediaId: $mediaId, "
            + ", ".join(assignments)
            + ") { id mediaId status progress score } }"
        )
        data = await self.client.execute(query, variables)
        entry = data.get("SaveMediaListEntry")
        if not isinstance(entry, dict):
            raise MetadataError("AniList did not return the updated list entry.")
        return entry
