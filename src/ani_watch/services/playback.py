"""Playback intelligence orchestration."""

from __future__ import annotations

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
