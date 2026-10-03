from pathlib import Path

from ani_watch.auth.anilist import AniListOAuth, TokenStore


def test_token_store_round_trip(tmp_path: Path) -> None:
    store = TokenStore(tmp_path / "token")
    store.save("secret-token")
    assert store.load() == "secret-token"
    store.clear()
    assert store.load() is None


def test_authorization_url_and_expiry() -> None:
    oauth = AniListOAuth("client", "secret", "http://localhost/callback")
    assert "client_id=client" in oauth.authorization_url()
    assert "response_type=code" in oauth.authorization_url()
    assert oauth.token_expiry("not-a-jwt") is None
