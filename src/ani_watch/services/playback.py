"""Playback intelligence orchestration."""

from collections.abc import Callable

from ani_watch.config.settings import PlaybackSettings
from ani_watch.domain.errors import PlaybackError
from ani_watch.player.vlc import VlcPlayer


class PlaybackHooks:
    """Optional timing hooks supplied by a metadata/provider layer."""

    def __init__(
        self,
        *,
        intro_end: Callable[[int], int | None] | None = None,
        outro_start: Callable[[int], int | None] | None = None,
    ) -> None:
        self.intro_end = intro_end
        self.outro_start = outro_start


class PlaybackManager:
    """Coordinate resume, auto-next, local preference and recovery."""

    def __init__(self, player: VlcPlayer, settings: PlaybackSettings) -> None:
        self.player = player
        self.settings = settings

    def start(self, uri: str, *, resume_seconds: int = 0) -> None:
        self.player.load(uri)
        if resume_seconds > 0:
            self.player.set_time(resume_seconds * 1000)
        self.player.set_volume(self.settings.volume)
        self.player.play()

    def seek(self, seconds: int) -> None:
        self.player.set_time(max(0, seconds) * 1000)

    def toggle_pause(self) -> None:
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def set_audio_track(self, track_id: int) -> None:
        self.player.select_audio_track(track_id)

    def set_subtitle_track(self, track_id: int) -> None:
        self.player.select_subtitle_track(track_id)

    def skip_intro(self, current_seconds: int, hooks: PlaybackHooks) -> None:
        if not self.settings.skip_intro or hooks.intro_end is None:
            return
        target = hooks.intro_end(current_seconds)
        if target is not None:
            self.seek(target)

    def skip_outro(self, current_seconds: int, hooks: PlaybackHooks) -> None:
        if not self.settings.skip_outro or hooks.outro_start is None:
            return
        target = hooks.outro_start(current_seconds)
        if target is not None:
            self.seek(target)

    def next_episode_index(self, current_index: int, total: int) -> int | None:
        """Return the next episode index when auto-next is enabled."""
        if not self.settings.auto_next:
            return None
        candidate = current_index + 1
        return candidate if 0 <= candidate < total else None

    def choose_local_first(
        self,
        local_uri: str | None,
        remote_uri: str | None,
    ) -> str | None:
        """Choose a local file before a provider URI when configured."""
        if self.settings.local_first and local_uri:
            return local_uri
        return remote_uri or local_uri

    def can_auto_next(self) -> bool:
        return self.settings.auto_next

    def quality(self) -> str:
        return self.settings.quality

    def should_prefer_local(self) -> bool:
        return self.settings.local_first

    def recover(self, uri: str) -> None:
        """Reload media after a recoverable player error."""
        try:
            self.player.stop()
            self.player.load(uri)
            self.player.play()
        except PlaybackError:
            raise
        except Exception as exc:
            raise PlaybackError("Playback recovery failed.") from exc


class PlaybackSession:
    """Bind playback, provider resolution, and local progress tracking."""

    def __init__(self, manager, resolver, library) -> None:
        self.manager = manager
        self.resolver = resolver
        self.library = library
        self._anime = None
        self._episode = None
        self._episode_index = 0
        self._total_episodes = 1
        self._completion_recorded = False

    async def start(self, anime, episode, *, episode_index: int = 0, total_episodes: int = 1):
        """Resolve and start an episode using the saved local progress."""
        from ani_watch.domain.models import EpisodeRef

        candidate = await self.resolver.resolve(
            anime,
            EpisodeRef(anime_id=anime.anilist_id, number=episode.number),
            quality=self.manager.quality(),
        )
        progress = self.library.progress.get(anime.anilist_id, episode.number)
        resume_seconds = 0
        if progress is not None and not progress.completed:
            resume_seconds = max(0, int(progress.position_seconds))

        self.manager.start(candidate.uri, resume_seconds=resume_seconds)
        self._anime = anime
        self._episode = episode
        self._episode_index = episode_index
        self._total_episodes = max(1, total_episodes)
        self._completion_recorded = False
        return candidate

    @property
    def active(self) -> bool:
        return self._anime is not None and self._episode is not None

    @property
    def current_index(self) -> int:
        return self._episode_index

    def save_progress(self, *, force_complete: bool = False) -> None:
        """Persist the current player position when a session is active."""
        if not self.active:
            return

        position_ms = max(0, int(self.manager.player.get_time()))
        duration_ms = max(0, int(self.manager.player.get_length()))
        position_seconds = position_ms // 1000
        duration_seconds = duration_ms // 1000 if duration_ms > 0 else None

        completed = (
            force_complete
            or self.manager.player.is_complete()
            or (
                duration_seconds is not None
                and duration_seconds > 0
                and position_seconds >= duration_seconds * 0.9
            )
        )
        if self._completion_recorded and not force_complete:
            return
        self.library.save_progress(
            self._anime.anilist_id,
            self._episode.number,
            position_seconds,
            duration_seconds,
        )
        if completed:
            self._completion_recorded = True

    def completion_pending(self) -> bool:
        """Return true when playback has completed and needs final persistence."""
        return self.active and self.manager.player.is_complete() and not self._completion_recorded

    def record_completion(self) -> None:
        """Persist a completed playback session exactly once."""
        if self.completion_pending():
            self.save_progress(force_complete=True)

    def next_episode_index(self, total: int) -> int | None:
        """Return the next episode index according to playback settings."""
        if not self.active:
            return None
        return self.manager.next_episode_index(self._episode_index, total)

    def stop(self) -> None:
        """Persist current progress and stop the active player."""
        if not self.active:
            return
        try:
            self.save_progress()
        finally:
            self.manager.player.stop()
            self._anime = None
            self._episode = None
            self._completion_recorded = False

    def close(self) -> None:
        """Stop active playback and release player resources."""
        self.stop()
        release = getattr(self.manager.player, "release", None)
        if callable(release):
            release()
