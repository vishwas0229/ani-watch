import json

import httpx
import pytest

from ani_watch.auth.anilist import AniListAccountService, AniListOAuth
from ani_watch.config.settings import AppSettings
from ani_watch.domain.errors import AuthenticationError
from ani_watch.domain.models import AnimeDetails
from ani_watch.metadata.anilist import AniListClient
from ani_watch.services.anilist_sync import AniListSyncService
from ani_watch.services.library import LibraryService
from ani_watch.storage.database import Database


def test_oauth_authorization_url() -> None:
    url = AniListOAuth.authorization_url("123", "http://localhost/callback")
    assert url.startswith("https://anilist.co/api/v2/oauth/authorize?")
    assert "client_id=123" in url
    assert "response_type=code" in url


def test_oauth_extracts_code_from_callback_url() -> None:
    callback = "http://localhost:8080/callback?code=abc123&state=ignored"
    assert AniListOAuth.extract_code(callback) == "abc123"
    assert AniListOAuth.extract_code("abc123") == "abc123"


@pytest.mark.asyncio
async def test_oauth_exchange_uses_mocked_http_and_returns_token() -> None:
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"access_token": "secret-token"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    oauth = AniListOAuth(client)
    try:
        token = await oauth.exchange_code(
            "client-id",
            "client-secret",
            "http://localhost/callback",
            "http://localhost/callback?code=oauth-code",
        )
    finally:
        await oauth.close()

    assert token == "secret-token"
    assert captured["code"] == "oauth-code"
    assert captured["client_id"] == "client-id"


class FakeTokenStore:
    def __init__(self) -> None:
        self.value: str | None = None

    def save(self, token: str) -> None:
        self.value = token

    def get(self) -> str | None:
        return self.value

    def clear(self) -> None:
        self.value = None


class FakeOAuth:
    def __init__(self) -> None:
        self.closed = False

    def authorization_url(self, client_id: str, redirect_uri: str) -> str:
        return f"https://example.test/login?client_id={client_id}&redirect_uri={redirect_uri}"

    async def exchange_code(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        code: str,
    ) -> str:
        assert (client_id, client_secret, redirect_uri, code) == (
            "id",
            "secret",
            "http://localhost/callback",
            "callback-code",
        )
        return "stored-token"

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_account_service_login_and_logout_use_token_store() -> None:
    token_store = FakeTokenStore()
    oauth = FakeOAuth()
    service = AniListAccountService(
        AppSettings(
            anilist_client_id="id",
            anilist_client_secret="secret",
            anilist_redirect_uri="http://localhost/callback",
        ),
        token_store=token_store,
        oauth=oauth,
    )

    assert not service.is_authenticated
    token = await service.login("callback-code")
    assert token == "stored-token"
    assert service.token() == "stored-token"
    assert service.is_authenticated

    service.logout()
    assert service.token() is None


@pytest.mark.asyncio
async def test_sync_reconciles_progress() -> None:
    assert AniListSyncService.reconcile_progress(3, 4) == 4
    assert AniListSyncService.reconcile_progress(3, 4, "local") == 3
    assert AniListSyncService.reconcile_progress(3, 4, "remote") == 4


@pytest.mark.asyncio
async def test_sync_rejects_missing_token() -> None:
    with pytest.raises(AuthenticationError):
        AniListSyncService("")


@pytest.mark.asyncio
async def test_sync_pull_merges_remote_progress_into_local_library(tmp_path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "MediaListCollection": {
                        "lists": [
                            {"entries": [{"mediaId": 100, "progress": 4}]},
                        ]
                    }
                }
            },
        )

    client = AniListClient(
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        retries=0,
        access_token="token",
    )
    database = Database(f"sqlite:///{tmp_path / 'sync.db'}")
    database.create_schema()
    library = LibraryService(database)
    sync = AniListSyncService("token", client=client)

    try:
        applied = await sync.pull_into_library(library, user_id=7)
    finally:
        await sync.close()
        database.dispose()

    assert applied == 1
    assert library.anime.get(100).title == "AniList #100"
    progress = library.progress.list_for_anime(100)
    assert progress[0].episode_number == 4
    assert progress[0].completed is True


@pytest.mark.asyncio
async def test_sync_pushes_maximum_local_progress(tmp_path) -> None:
    pushed: list[dict] = []

    class FakeClient:
        async def request(self, query, variables):
            pushed.append({"query": query, "variables": variables})
            return {"SaveMediaListEntry": variables}

        async def close(self):
            return

    database = Database(f"sqlite:///{tmp_path / 'sync.db'}")
    database.create_schema()
    library = LibraryService(database)
    library.anime.upsert(AnimeDetails(anilist_id=100, title="Sample"))
    library.progress.save(100, 3, 60, 120, completed=False)
    library.progress.save(100, 4, 120, 120, completed=True)
    sync = AniListSyncService("token", client=FakeClient())

    try:
        count = await sync.push_library_progress(library)
    finally:
        await sync.close()
        database.dispose()

    assert count == 1
    assert pushed[0]["variables"] == {"mediaId": 100, "progress": 4}
