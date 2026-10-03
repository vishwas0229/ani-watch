"""Playback orchestration and intelligence."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from ani_watch.config.settings import PlaybackSettings, ProviderSettings
from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.history import WatchHistoryEntry
from ani_watch.domain.models import AnimeRef
from ani_watch.providers.registry import ProviderRegistry

from .vlc import VlcPlayer


class PlaybackManager:
    """Resolve, resume, play, recover, and advance episodes."""

    def __init__(
        self,
        player: VlcPlayer,
        providers: ProviderRegistry,
        settings: PlaybackSettings,
        provider_settings: ProviderSettings | None = None,
    ) -> None:
        self.player = player
        self.providers = providers
        self.settings = settings
        self.provider_settings = provider_settings
        self.current: EpisodeItem | None = None
        self.current_anime: AnimeRef | None = None
        self._next: Callable[[], None] | None = None

        self.player.on_complete(self._handle_complete)

    async def play(
        self,
        anime: AnimeRef,
        episode_number: int,
        *,
        history: Sequence[WatchHistoryEntry] = (),
    ) -> EpisodeItem:
        """Resolve an episode and resume from matching local history."""
        preferred = self._preferred_providers()
        episode = await self.providers.resolve(
            anime,
            episode_number,
            preferred=preferred,
        )
        self.current = episode
        self.current_anime = anime

        if not episode.source_uri:
            raise FileNotFoundError("The selected episode has no playable source.")

        self.player.load(
            episode.source_uri,
            options=(" :network-caching=1000".strip(),),
        )

        resume_at = self._resume_position(history, anime.anilist_id, episode_number)
        if resume_at > 0:
            self.player.seek(resume_at)

        self.player.set_volume(self.settings.volume)
        self.player.play()
        return episode

    def pause(self) -> None:
        self.player.pause()

    def resume(self) -> None:
        self.player.play()

    def stop(self) -> None:
        self.player.stop()

    def seek_relative(self, seconds: int) -> None:
        self.player.seek(self.player.position() + seconds)

    def set_next_callback(self, callback: Callable[[], None] | None) -> None:
        """Register auto-next behavior."""
        self._next = callback

    def recover(self) -> None:
        """Retry the current episode after a player failure."""
        if self.current and self.current.source_uri:
            self.player.load(self.current.source_uri)
            self.player.play()

    def skip_intro(self) -> None:
        """Skip configured intro duration."""
        if self.settings.skip_intro and self.settings.intro_seconds:
            self.player.seek(self.settings.intro_seconds)

    def skip_outro(self, duration_seconds: int | None = None) -> None:
        """Skip toward the end of the configured outro window."""
        if self.settings.skip_outro and self.settings.outro_seconds and duration_seconds:
            self.player.seek(max(0, duration_seconds - self.settings.outro_seconds))

    def _handle_complete(self) -> None:
        """Advance automatically when the current item finishes."""
        if self.settings.auto_next and self._next is not None:
            self._next()

    def _preferred_providers(self) -> tuple[str, ...] | None:
        if self.provider_settings is None:
            return None
        providers = tuple(self.provider_settings.enabled)
        if self.settings.local_first and "local" in providers:
            return ("local",) + tuple(name for name in providers if name != "local")
        return providers

    @staticmethod
    def _resume_position(
        history: Sequence[WatchHistoryEntry],
        anime_id: int,
        episode_number: int,
    ) -> int:
        """Find a recent position for the requested episode."""
        for entry in history:
            if entry.anime_id == anime_id and entry.episode_number == episode_number:
                return max(0, entry.progress_seconds)
        return 0
