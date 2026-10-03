"""AniList OAuth helpers and protected token storage."""

from __future__ import annotations

import base64
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlencode

import httpx
from platformdirs import user_config_path

from ani_watch.domain.errors import MetadataError


class TokenStore:
    """Store one AniList token in a permissions-protected user file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or user_config_path("ani-watch") / "anilist-token"

    def load(self) -> str | None:
        if not self.path.exists():
            return None
        return self.path.read_text(encoding="utf-8").strip() or None

    def save(self, token: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".anilist-", dir=self.path.parent)
        try:
            os.write(fd, token.encode("utf-8"))
        finally:
            os.close(fd)
        temporary = Path(temp_name)
        temporary.replace(self.path)
        if os.name == "posix":
            self.path.chmod(0o600)

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            return


class AniListOAuth:
    """Build OAuth URLs and exchange an authorization code."""

    authorize_url = "https://anilist.co/api/v2/oauth/authorize"
    token_url = "https://anilist.co/api/v2/oauth/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str | None,
        redirect_uri: str,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def authorization_url(self) -> str:
        """Return the authorization-code grant URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }
        return self.authorize_url + "?" + urlencode(params)

    async def exchange_code(self, code: str) -> str:
        """Exchange an authorization code for an access token."""
        if not self.client_secret:
            raise MetadataError("AniList client secret is required for code exchange.")
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self.token_url,
                json=payload,
                headers={"Accept": "application/json"},
            )
        if response.is_error:
            raise MetadataError("AniList OAuth token exchange failed.")
        token = response.json().get("access_token")
        if not token:
            raise MetadataError("AniList did not return an access token.")
        return str(token)

    @staticmethod
    def token_expiry(token: str) -> int | None:
        """Read the JWT expiration claim without a JWT dependency."""
        parts = token.split(".")
        if len(parts) != 3:
            return None
        try:
            encoded = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(encoded))
        except (ValueError, json.JSONDecodeError):
            return None
        value = payload.get("exp")
        return int(value) if isinstance(value, (int, float)) else None
