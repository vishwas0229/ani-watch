"""AniList watch-list synchronization service."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ani_watch.services.library import LibraryService


from ani_watch.domain.errors import AuthenticationError, MetadataError
from ani_watch.domain.models import AnimeDetails
from ani_watch.storage.database import Database
from ani_watch.storage.repositories import ProgressRepository
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

    def __init__(
        self,
        access_token: str,
        *,
        client: AniListClient | None = None,
        timeout: float = 10.0,
        retries: int = 3,
    ) -> None:
        if not access_token:
            raise AuthenticationError("AniList access token is required.")
        self.client = client or AniListClient(
            access_token=access_token,
            timeout=timeout,
            retries=retries,
        )

    async def close(self) -> None:
        """Close the underlying AniList client."""
        await self.client.close()

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

    async def pull_into_library(
        self,
        library: "LibraryService",
        user_id: int,
    ) -> int:
        """Merge remote AniList episode progress into local persistence."""
        entries = await self.pull_watch_list(user_id)
        applied = 0

        for entry in entries:
            media_id = self._positive_int(entry.get("mediaId"))
            if media_id is None:
                continue

            remote_progress = max(0, self._positive_int(entry.get("progress")) or 0)
            anime = library.anime.get(media_id)
            if anime is None:
                library.anime.upsert(
                    AnimeDetails(
                        anilist_id=media_id,
                        title=f"AniList #{media_id}",
                    )
                )

            local_rows = library.progress.list_for_anime(media_id)
            local_progress = self.local_episode_progress(local_rows)
            merged = self.reconcile_progress(local_progress, remote_progress)

            if merged > local_progress:
                library.progress.save(
                    media_id,
                    merged,
                    0,
                    None,
                    completed=True,
                )
                applied += 1

        return applied

    async def push_library_progress(self, library: "LibraryService") -> int:
        """Push local watch progress to AniList, grouped per media item."""
        grouped: dict[int, int] = {}
        for record in library.progress.list_all():
            progress = record.episode_number
            if not record.completed:
                progress = max(0, progress - 1)
            grouped[record.anime_id] = max(grouped.get(record.anime_id, 0), progress)

        pushed = 0
        for media_id, progress in grouped.items():
            await self.push_progress(media_id, progress)
            pushed += 1
        return pushed

    @staticmethod
    def local_episode_progress(records: list[Any]) -> int:
        """Convert per-episode local rows to an AniList-style progress count."""
        progress = 0
        for record in records:
            episode = max(0, int(record.episode_number))
            progress = max(
                progress,
                episode if record.completed else max(0, episode - 1),
            )
        return progress

    @staticmethod
    def _positive_int(value: Any) -> int | None:
        try:
            integer = int(value)
        except (TypeError, ValueError):
            return None
        return integer if integer >= 0 else None

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
