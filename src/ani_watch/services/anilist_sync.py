"""AniList watch-list synchronization service."""

from typing import Any

from ani_watch.domain.errors import AuthenticationError, MetadataError
from ani_watch.metadata.anilist import AniListClient

WATCH_LIST_QUERY = """
query ($userId: Int) {
  MediaListCollection(userId: $userId, type: ANIME) {
    lists { entries { mediaId status score progress } }
  }
}
"""

SAVE_PROGRESS = """
mutation ($mediaId: Int!, $progress: Int) {
  SaveMediaListEntry(mediaId: $mediaId, progress: $progress) {
    id mediaId progress
  }
}
"""

SAVE_STATUS = """
mutation ($mediaId: Int!, $status: MediaListStatus) {
  SaveMediaListEntry(mediaId: $mediaId, status: $status) {
    id mediaId status
  }
}
"""

SAVE_SCORE = """
mutation ($mediaId: Int!, $score: Float) {
  SaveMediaListEntry(mediaId: $mediaId, score: $score) {
    id mediaId score
  }
}
"""

VIEWER_QUERY = "query { Viewer { id name } }"


class AniListSyncService:
    """Pull and push a user's AniList media-list state."""

    def __init__(self, access_token: str) -> None:
        if not access_token:
            raise AuthenticationError("AniList access token is required.")
        self.client = AniListClient(access_token=access_token)

    async def viewer(self) -> dict[str, Any]:
        data = await self.client.request(VIEWER_QUERY)
        viewer = data.get("Viewer")
        if not isinstance(viewer, dict):
            raise AuthenticationError("AniList viewer could not be loaded.")
        return viewer

    async def pull_watch_list(self, user_id: int) -> list[dict[str, Any]]:
        data = await self.client.request(WATCH_LIST_QUERY, {"userId": user_id})
        collection = data.get("MediaListCollection") or {}
        return [
            entry
            for group in collection.get("lists", [])
            for entry in group.get("entries", [])
            if isinstance(entry, dict)
        ]

    async def push_progress(self, media_id: int, progress: int) -> dict[str, Any]:
        return await self._mutate(
            SAVE_PROGRESS,
            {"mediaId": media_id, "progress": max(0, progress)},
        )

    async def update_status(self, media_id: int, status: str) -> dict[str, Any]:
        return await self._mutate(SAVE_STATUS, {"mediaId": media_id, "status": status})

    async def update_score(self, media_id: int, score: float) -> dict[str, Any]:
        if not 0 <= score <= 10:
            raise ValueError("AniList score must be between 0 and 10.")
        return await self._mutate(SAVE_SCORE, {"mediaId": media_id, "score": score})

    @staticmethod
    def reconcile_progress(local: int, remote: int, prefer: str = "latest") -> int:
        """Resolve a local/remote progress conflict deterministically."""
        if prefer == "local":
            return local
        if prefer == "remote":
            return remote
        return max(local, remote)

    async def _mutate(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        data = await self.client.request(query, variables)
        for value in data.values():
            if isinstance(value, dict):
                return value
        raise MetadataError("AniList mutation returned no result.")
