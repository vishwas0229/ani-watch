import asyncio

import pytest
from typer.testing import CliRunner

from ani_watch.cli.main import app


class FakeOAuth:
    async def close(self) -> None:
        return


class FakeAccount:
    def __init__(self, settings) -> None:
        self.oauth = FakeOAuth()
        self.logged_in = False

    @property
    def is_authenticated(self) -> bool:
        return self.logged_in

    def authorization_url(self, *, client_id=None, redirect_uri=None) -> str:
        return (
            "https://anilist.co/api/v2/oauth/authorize"
            f"?client_id={client_id}&redirect_uri={redirect_uri}"
        )

    async def login(self, code, *, client_id=None, client_secret=None, redirect_uri=None):
        assert code == "callback-code"
        self.logged_in = True
        return "token"


@pytest.fixture
def conda(monkeypatch):
    monkeypatch.setenv("CONDA_PREFIX", "/opt/conda/envs/ani-watch")


def test_auth_help_lists_supported_commands(conda) -> None:
    result = CliRunner().invoke(app, ["auth", "--help"])
    assert result.exit_code == 0
    assert "login" in result.stdout
    assert "logout" in result.stdout
    assert "status" in result.stdout
    assert "sync" in result.stdout


def test_auth_login_accepts_callback_url_and_stores_token(conda, monkeypatch) -> None:
    account = FakeAccount(None)
    monkeypatch.setattr("ani_watch.cli.main.AniListAccountService", lambda settings: account)

    result = CliRunner().invoke(
        app,
        [
            "auth",
            "login",
            "--client-id",
            "client-id",
            "--client-secret",
            "client-secret",
            "--redirect-uri",
            "http://localhost/callback",
            "--code",
            "http://localhost/callback?code=callback-code",
        ],
    )

    assert result.exit_code == 0
    assert "login successful" in result.stdout.lower()
    assert account.logged_in


def test_auth_logout_clears_credentials(conda, monkeypatch) -> None:
    class Account:
        def __init__(self, settings) -> None:
            self.cleared = False

        def logout(self) -> None:
            self.cleared = True

    account = Account(None)
    monkeypatch.setattr("ani_watch.cli.main.AniListAccountService", lambda settings: account)

    result = CliRunner().invoke(app, ["auth", "logout"])

    assert result.exit_code == 0
    assert "logout successful" in result.stdout.lower()
    assert account.cleared
