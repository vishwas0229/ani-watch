import pytest

from ani_watch.auth.conflicts import SyncConflict, resolve_progress_conflict
from ani_watch.auth.sync import AniListSyncService


class FakeClient:
    async def execute(self, query, variables=None):
        if "Viewer" in query:
            return {"Viewer": {"id": 42}}
        if "SaveMediaListEntry" in query:
            return {"SaveMediaListEntry": {"id": 10, "mediaId": 100, "progress": 5}}
        return {
            "MediaListCollection": {
                "lists": [
                    {
                        "entries": [
                            {
                                "mediaId": 100,
                                "status": "CURRENT",
                                "progress": 4,
                                "score": 8.0,
                                "media": {
                                    "title": {"english": "Example", "romaji": "Example"}
                                },
                            }
                        ]
                    }
                ]
            }
        }


@pytest.mark.asyncio
async def test_anilist_sync_pull_and_mutations() -> None:
    service = AniListSyncService(FakeClient())

    assert await service.viewer_id() == 42
    entries = await service.pull_watch_list()
    assert entries[0].media_id == 100
    assert entries[0].progress == 4
    assert (await service.push_progress(100, 5))["progress"] == 5
    assert (await service.update_status(100, "COMPLETED"))["mediaId"] == 100


def test_sync_conflict_resolution_is_explicit() -> None:
    conflict = SyncConflict(100, 4, 6, "CURRENT", "COMPLETED")
    assert resolve_progress_conflict(conflict, "local") == 4
    assert resolve_progress_conflict(conflict, "remote") == 6
    assert resolve_progress_conflict(conflict, "max") == 6
