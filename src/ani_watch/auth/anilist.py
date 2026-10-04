"""AniList OAuth2 token storage and authorization helpers."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import keyring

from ani_watch.config.settings import AppSettings
from ani_watch.domain.errors import AuthenticationError


class AniListTokenStore:
    """Store an AniList access token in the OS credential store."""

    SERVICE = "ani-watch"
    KEY = "anilist-access-token"

    def save(self, token: str) -> None:
        keyring.set_password(self.SERVICE, self.KEY, token)

    def get(self) -> str | None:
        return keyring.get_password(self.SERVICE, self.KEY)

    def clear(self) -> None:
        try:
            keyring.delete_password(self.SERVICE, self.KEY)
        except keyring.errors.PasswordDeleteError:
            pass


class AniListOAuth:
    """Build authorization URLs and exchange auth codes."""

    AUTHORIZE_URL = "https://anilist.co/api/v2/oauth/authorize"
    TOKEN_URL = "https://anilist.co/api/v2/oauth/token"

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client

    @classmethod
    def authorization_url(cls, client_id: str, redirect_uri: str) -> str:
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
        }
        return f"{cls.AUTHORIZE_URL}?{urlencode(params)}"

    @classmethod
    def extract_code(cls, value: str) -> str:
        """Extract an OAuth code from a raw code or callback URL."""
        value = value.strip()
        if not value:
            raise AuthenticationError("An AniList authorization code is required.")

        parsed = urlparse(value)
        if parsed.query:
            code = parse_qs(parsed.query).get("code", [None])[0]
            if code:
                return str(code)

        if parsed.fragment:
            code = parse_qs(parsed.fragment).get("code", [None])[0]
            if code:
                return str(code)

        if "://" in value:
            raise AuthenticationError("The callback URL does not contain an authorization code.")
        return value

    async def exchange_code(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        code: str,
    ) -> str:
        """Exchange an authorization code for an access token."""
        code = self.extract_code(code)
        if not client_id or not client_secret or not redirect_uri:
            raise AuthenticationError(
                "AniList client ID, client secret, and redirect URI are required."
            )

        owned = self._client is None
        client = self._client or httpx.AsyncClient(timeout=15)
        try:
            response = await client.post(
                self.TOKEN_URL,
                json={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
            token = response.json().get("access_token")
        except (httpx.HTTPError, ValueError) as exc:
            raise AuthenticationError("AniList OAuth token exchange failed.") from exc
        finally:
            if owned:
                await client.aclose()

        if not token:
            raise AuthenticationError("AniList did not return an access token.")
        return str(token)

    async def close(self) -> None:
        """Close an injected client when it is owned by the OAuth helper."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class AniListAccountService:
    """Coordinate AniList OAuth credentials and authenticated account state."""

    def __init__(
        self,
        settings: AppSettings,
        *,
        token_store: AniListTokenStore | None = None,
        oauth: AniListOAuth | None = None,
    ) -> None:
        self.settings = settings
        self.token_store = token_store or AniListTokenStore()
        self.oauth = oauth or AniListOAuth()

    @property
    def is_authenticated(self) -> bool:
        """Return whether an AniList access token is stored."""
        return bool(self.token_store.get())

    def authorization_url(
        self,
        *,
        client_id: str | None = None,
        redirect_uri: str | None = None,
    ) -> str:
        """Build a login URL from explicit values or application settings."""
        resolved_client_id = client_id or self.settings.anilist_client_id
        resolved_redirect = redirect_uri or self.settings.anilist_redirect_uri
        if not resolved_client_id or not resolved_redirect:
            raise AuthenticationError("AniList client ID and redirect URI are required for login.")
        return self.oauth.authorization_url(resolved_client_id, resolved_redirect)

    async def login(
        self,
        code: str,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
    ) -> str:
        """Exchange an authorization code and securely store the token."""
        resolved_client_id = client_id or self.settings.anilist_client_id
        resolved_secret = client_secret or self.settings.anilist_client_secret
        resolved_redirect = redirect_uri or self.settings.anilist_redirect_uri
        if not resolved_client_id or not resolved_secret or not resolved_redirect:
            raise AuthenticationError(
                "AniList client ID, client secret, and redirect URI are required."
            )

        token = await self.oauth.exchange_code(
            resolved_client_id,
            resolved_secret,
            resolved_redirect,
            code,
        )
        self.token_store.save(token)
        return token

    def logout(self) -> None:
        """Remove the stored AniList access token."""
        self.token_store.clear()

    def token(self) -> str | None:
        """Return the stored access token for authenticated service calls."""
        return self.token_store.get()
