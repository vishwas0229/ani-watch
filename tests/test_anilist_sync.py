import httpx
import pytest

from ani_watch.auth.anilist import AniListOAuth
from ani_watch.domain.errors import AuthenticationError
from ani_watch.services.anilist_sync import AniListSyncService


def test_oauth_authorization_url() -> None:
    url = AniListOAuth.authorization_url("123", "http://localhost/callback")
    assert url.startswith("https://anilist.co/api/v2/oauth/authorize?")
    assert "client_id=123" in url
    assert "response_type=code" in url


@pytest.mark.asyncio
async def test_sync_reconciles_progress() -> None:
    assert AniListSyncService.reconcile_progress(3, 4) == 4
    assert AniListSyncService.reconcile_progress(3, 4, "local") == 3
    assert AniListSyncService.reconcile_progress(3, 4, "remote") == 4


@pytest.mark.asyncio
async def test_sync_rejects_missing_token() -> None:
    with pytest.raises(AuthenticationError):
        AniListSyncService("")
