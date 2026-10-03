"""AniList OAuth2 token storage and authorization helpers."""

from urllib.parse import urlencode

import httpx
import keyring

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

    @classmethod
    def authorization_url(cls, client_id: str, redirect_uri: str) -> str:
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
        }
        return f"{cls.AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        code: str,
    ) -> str:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
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

        if not token:
            raise AuthenticationError("AniList did not return an access token.")
        return str(token)
