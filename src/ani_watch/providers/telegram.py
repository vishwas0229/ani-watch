"""Telegram-backed provider for user-owned and authorized media."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from ani_watch.auth.telegram import TelegramAccountService, TelegramCredentialStore
from ani_watch.config.settings import AppSettings
from ani_watch.domain.errors import ProviderError
from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.providers.telegram_gateway import TelegramStreamingGateway


class TelegramMediaProvider:
    """Resolve AniList episodes to matching authorized Telegram channel media."""

    name = "telegram"
    _anime_tag = re.compile(
        r"(?:^|[\s\[({])(?:anilist(?:[_ -]?id)?|anime(?:[_ -]?id)?)\s*[:=]\s*(\d+)",
        re.IGNORECASE,
    )
    _episode_tag = re.compile(
        r"(?:^|[\s\[({])(?:episode|ep)\s*[:=#-]?\s*(\d{1,4})",
        re.IGNORECASE,
    )
    _episode_label = re.compile(
        r"(?:^|[\s._-])(?:episode|ep|e)\s*[-_.:# ]*\s*(\d{1,4})(?:$|[\s._-])",
        re.IGNORECASE,
    )

    def __init__(
        self,
        settings: AppSettings,
        *,
        credential_store: TelegramCredentialStore | None = None,
        account_service: TelegramAccountService | None = None,
        client_factory: Callable[..., Any] | None = None,
        scan_limit: int | None = None,
    ) -> None:
        self.settings = settings
        self.credentials = credential_store or TelegramCredentialStore()
        self.account = account_service or TelegramAccountService(
            settings,
            credential_store=self.credentials,
        )
        self._client_factory = client_factory
        self.scan_limit = max(1, int(scan_limit or settings.telegram_scan_limit))
        self._gateway: TelegramStreamingGateway | None = None
        self._channel: Any | None = None

    @property
    def configured(self) -> bool:
        try:
            api_hash = self.credentials.get_api_hash()
        except Exception:
            api_hash = None
        return bool(
            self.settings.telegram_api_id
            and self.settings.telegram_channel
            and api_hash
        )

    async def available(self, anime: AnimeRef, episode: EpisodeRef) -> bool:
        """Return whether Telegram is configured as a potential playback source."""
        return self.configured

    async def _client(self):
        if self._client_factory is not None and getattr(self.account, "_client", None) is None:
            api_id = self.settings.telegram_api_id
            api_hash = self.credentials.get_api_hash()
            if api_id is None or not api_hash:
                raise ProviderError(
                    "Telegram is not configured. Set the API ID, API hash, and channel in Settings."
                )
            self.account._client = self._client_factory(
                str(self.account.session_path),
                api_id,
                api_hash,
            )
        try:
            return await self.account.connect()
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(str(exc)) from exc

    async def _entity(self):
        if self._channel is not None:
            return self._channel
        channel = self.settings.telegram_channel
        if not channel:
            raise ProviderError(
                "Telegram channel is not configured. Set Settings → Telegram channel."
            )
        client = await self._client()
        try:
            self._channel = await client.get_entity(channel)
        except Exception as exc:
            raise ProviderError(
                f"Telegram channel '{channel}' could not be opened: {exc}"
            ) from exc
        return self._channel

    @classmethod
    def _text(cls, message: Any) -> str:
        raw_text = getattr(message, "raw_text", None)
        text = getattr(message, "text", None)
        values = [raw_text, text, getattr(getattr(message, "file", None), "name", None)]
        return " ".join(str(value).strip() for value in values if value).strip()

    @classmethod
    def _file_name(cls, message: Any) -> str:
        file = getattr(message, "file", None)
        name = getattr(file, "name", None)
        return str(name).strip() if name else "telegram-media"

    @classmethod
    def _file_size(cls, message: Any) -> int:
        file = getattr(message, "file", None)
        try:
            value = int(getattr(file, "size", 0) or 0)
        except (TypeError, ValueError):
            return 0
        return max(0, value)

    @classmethod
    def _mime_type(cls, message: Any) -> str:
        file = getattr(message, "file", None)
        value = getattr(file, "mime_type", None)
        return str(value).strip() if value else "application/octet-stream"

    @classmethod
    def _is_streamable_media(cls, message: Any) -> bool:
        file = getattr(message, "file", None)
        mime_type = str(getattr(file, "mime_type", "") or "").casefold()
        if mime_type.startswith("video/"):
            return True
        if getattr(message, "video", None) is not None:
            return True
        name = cls._file_name(message).casefold()
        return name.endswith((".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi", ".ts"))

    @classmethod
    def _anime_id_tag(cls, text: str) -> int | None:
        match = cls._anime_tag.search(text)
        return int(match.group(1)) if match else None

    @classmethod
    def _episode_tag_value(cls, text: str) -> int | None:
        match = cls._episode_tag.search(text)
        return int(match.group(1)) if match else None

    @classmethod
    def _episode_number(cls, text: str) -> int | None:
        tagged = cls._episode_tag_value(text)
        if tagged is not None:
            return tagged
        match = cls._episode_label.search(text)
        return int(match.group(1)) if match else None

    @staticmethod
    def _normalized(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

    @classmethod
    def _title_matches(cls, anime_title: str, text: str) -> bool:
        title = cls._normalized(anime_title)
        target = cls._normalized(text)
        if not title or not target:
            return False
        if title in target:
            return True
        title_words = {word for word in title.split() if len(word) > 1}
        target_words = set(target.split())
        if not title_words:
            return False
        overlap = len(title_words & target_words) / len(title_words)
        return overlap >= 0.8

    @classmethod
    def _matches(
        cls,
        message: Any,
        anime: AnimeRef,
        episode: EpisodeRef,
    ) -> bool:
        text = cls._text(message)
        explicit_anime_id = cls._anime_id_tag(text)
        if explicit_anime_id is not None:
            return (
                explicit_anime_id == anime.anilist_id
                and cls._episode_number(text) == episode.number
            )

        return (
            cls._title_matches(anime.title, text)
            and cls._episode_number(text) == episode.number
        )

    async def _find_message(self, anime: AnimeRef, episode: EpisodeRef):
        entity = await self._entity()
        client = await self._client()
        selected = None
        async for message in client.iter_messages(entity, limit=self.scan_limit):
            if self._file_size(message) <= 0:
                continue
            if self._matches(message, anime, episode):
                if selected is None or int(getattr(message, "id", 0) or 0) > int(
                    getattr(selected, "id", 0) or 0
                ):
                    selected = message
        if selected is None:
            raise ProviderError(
                f"No Telegram media matched '{anime.title}' Episode {episode.number}. "
                "Use a caption such as 'anilist_id=123 episode=1' for an exact mapping."
            )
        return selected

    async def list_media(self, *, limit: int | None = None) -> list[dict[str, object]]:
        """List video/document media currently visible in the configured channel."""
        entity = await self._entity()
        client = await self._client()
        results: list[dict[str, object]] = []
        async for message in client.iter_messages(entity, limit=limit or self.scan_limit):
            size = self._file_size(message)
            if size <= 0 or not self._is_streamable_media(message):
                continue
            file = getattr(message, "file", None)
            duration = getattr(file, "duration", None)
            results.append(
                {
                    "message_id": int(getattr(message, "id", 0) or 0),
                    "filename": self._file_name(message),
                    "size": size,
                    "mime_type": self._mime_type(message),
                    "duration_seconds": int(duration) if duration is not None else None,
                    "text": getattr(message, "text", None) or "",
                }
            )
        return results

    async def resolve(
        self,
        anime: AnimeRef,
        episode: EpisodeRef,
        *,
        quality: str | None = None,
    ) -> MediaCandidate | None:
        """Resolve a matching Telegram message into a local Range-capable HTTP URL."""
        message = await self._find_message(anime, episode)
        client = await self._client()
        if self._gateway is None:
            self._gateway = TelegramStreamingGateway(client)
            await self._gateway.start()

        size = self._file_size(message)
        filename = self._file_name(message)
        mime_type = self._mime_type(message)
        uri = self._gateway.register(
            message,
            size=size,
            mime_type=mime_type,
            filename=filename,
        )
        return MediaCandidate(
            uri=uri,
            provider=self.name,
            quality=quality,
        )

    async def close(self) -> None:
        """Stop the local gateway and close the Telegram client."""
        if self._gateway is not None:
            await self._gateway.close()
            self._gateway = None
        await self.account.close()
