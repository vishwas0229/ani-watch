"""Optional VLC/libVLC player adapter."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ani_watch.domain.errors import PlaybackError


class VlcPlayer:
    """Wrap python-vlc while keeping the player dependency optional."""

    def __init__(self, args: tuple[str, ...] = ()) -> None:
        try:
            import vlc
        except ImportError as exc:
            raise PlaybackError(
                "python-vlc is not installed. Install the project environment first."
            ) from exc

        self._vlc = vlc
        try:
            self.instance = vlc.Instance(*args)
            self.player = self.instance.media_player_new()
        except Exception as exc:
            raise PlaybackError(
                "libVLC could not be initialized. Ensure VLC is installed on the system."
            ) from exc
        self._end_callback: Callable[[], None] | None = None
        self.quality = "1080p"

    def load(self, uri: str, *, options: tuple[str, ...] = ()) -> None:
        """Load a local path or URI."""
        try:
            media = self.instance.media_new(uri)
            for option in options:
                media.add_option(option)
            self.player.set_media(media)
        except Exception as exc:
            raise PlaybackError(f"Unable to load media: {uri}") from exc

    def play(self) -> None:
        if self.player.play() == -1:
            raise PlaybackError("VLC failed to start playback.")

    def pause(self) -> None:
        self.player.pause()

    def stop(self) -> None:
        self.player.stop()

    def toggle_pause(self) -> None:
        self.player.pause()

    def seek(self, seconds: int) -> None:
        if self.player.set_time(max(0, int(seconds))) == -1:
            raise PlaybackError("VLC could not seek to the requested position.")

    def set_volume(self, volume: int) -> None:
        value = max(0, min(int(volume), 100))
        if self.player.audio_set_volume(value) == -1:
            raise PlaybackError("VLC could not set the requested volume.")

    def position(self) -> int:
        value = self.player.get_time()
        return max(0, int(value or 0) // 1000)

    def duration(self) -> int:
        value = self.player.get_length()
        return max(0, int(value or 0) // 1000)

    def audio_tracks(self) -> list[tuple[int, str]]:
        """Return available audio track IDs and labels."""
        values = self.player.audio_get_track_description() or []
        return [(int(track_id), self._decode(label)) for track_id, label in values]

    def set_audio_track(self, track_id: int) -> None:
        if self.player.audio_set_track(int(track_id)) == -1:
            raise PlaybackError(f"Unable to select audio track {track_id}.")

    def subtitle_tracks(self) -> list[tuple[int, str]]:
        """Return available subtitle track IDs and labels."""
        values = self.player.video_get_spu_description() or []
        return [(int(track_id), self._decode(label)) for track_id, label in values]

    def set_subtitle_track(self, track_id: int) -> None:
        if self.player.video_set_spu(int(track_id)) == -1:
            raise PlaybackError(f"Unable to select subtitle track {track_id}.")

    def set_quality(self, quality: str) -> None:
        """Store the requested quality for provider/source adapters."""
        clean = quality.strip()
        if clean:
            self.quality = clean

    def on_complete(self, callback: Callable[[], None]) -> None:
        """Register a completion callback."""
        self._end_callback = callback

        def handle(_: Any) -> None:
            if self._end_callback:
                self._end_callback()

        self.player.event_manager().event_attach(
            self._vlc.EventType.MediaPlayerEndReached,
            handle,
        )

    @staticmethod
    def uri_for_path(path: str | Path) -> str:
        """Convert a local path to a file URI."""
        return Path(path).expanduser().resolve().as_uri()

    @staticmethod
    def _decode(value: object) -> str:
        return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
