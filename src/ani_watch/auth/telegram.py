"""Telegram account credentials and session helpers.

Telegram is used only as an authorized media source. API credentials live in the
OS keyring and the MTProto session is kept under the platform data directory.
"""

from __future__ import annotations

from pathlib import Path

import keyring
from platformdirs import user_data_path
from telethon import TelegramClient

from ani_watch.config.settings import AppSettings
from ani_watch.domain.errors import AuthenticationError


class TelegramCredentialStore:
    """Store the Telegram API hash in the OS credential store."""

    SERVICE = "ani-watch"
    API_HASH_KEY = "telegram-api-hash"

    def save_api_hash(self, api_hash: str) -> None:
        value = api_hash.strip()
        if not value:
            raise ValueError("Telegram API hash cannot be empty.")
        keyring.set_password(self.SERVICE, self.API_HASH_KEY, value)

    def get_api_hash(self) -> str | None:
        value = keyring.get_password(self.SERVICE, self.API_HASH_KEY)
        return value.strip() if value else None

    def clear_api_hash(self) -> None:
        try:
            keyring.delete_password(self.SERVICE, self.API_HASH_KEY)
        except keyring.errors.PasswordDeleteError:
            pass


class TelegramAccountService:
    """Create and authenticate the local Telegram MTProto session."""

    def __init__(
        self,
        settings: AppSettings,
        *,
        credential_store: TelegramCredentialStore | None = None,
        session_path: Path | None = None,
    ) -> None:
        self.settings = settings
        self.credentials = credential_store or TelegramCredentialStore()
        data_dir = user_data_path("ani-watch") / "telegram"
        self.session_path = session_path or data_dir / "ani_watch"
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self._client: TelegramClient | None = None

    def _validate_configuration(self) -> tuple[int, str]:
        api_id = self.settings.telegram_api_id
        api_hash = self.credentials.get_api_hash()
        if api_id is None or api_id <= 0:
            raise AuthenticationError(
                "Telegram API ID is not configured. Run 'ani-watch telegram configure'."
            )
        if not api_hash:
            raise AuthenticationError(
                "Telegram API hash is not configured. Run 'ani-watch telegram configure'."
            )
        return api_id, api_hash

    def client(self) -> TelegramClient:
        """Return a lazily-created TelegramClient bound to the persistent session."""
        if self._client is None:
            api_id, api_hash = self._validate_configuration()
            self._client = TelegramClient(
                str(self.session_path),
                api_id,
                api_hash,
            )
        return self._client

    async def connect(self) -> TelegramClient:
        """Connect using the stored session without prompting for a login."""
        client = self.client()
        if not client.is_connected():
            await client.connect()
        if not await client.is_user_authorized():
            raise AuthenticationError(
                "Telegram account is not authorized. Run 'ani-watch telegram login' first."
            )
        return client

    async def login(self, phone: str | None = None) -> None:
        """Authenticate the account interactively and persist the MTProto session."""
        client = self.client()
        try:
            if phone:
                await client.start(phone=phone.strip())
            else:
                await client.start()
        except Exception as exc:
            raise AuthenticationError(f"Telegram login failed: {exc}") from exc

    async def status(self) -> tuple[bool, str | None]:
        """Return authorization state and the connected account's display name."""
        client = await self.connect()
        me = await client.get_me()
        if me is None:
            return False, None
        first = str(getattr(me, "first_name", "") or "").strip()
        last = str(getattr(me, "last_name", "") or "").strip()
        name = " ".join(part for part in (first, last) if part) or None
        username = getattr(me, "username", None)
        if username:
            name = f"{name or ''} (@{username})".strip()
        return True, name

    async def close(self) -> None:
        """Disconnect the Telegram client when Ani-Watch exits."""
        if self._client is not None:
            await self._client.disconnect()
            self._client = None
