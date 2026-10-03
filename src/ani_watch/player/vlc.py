"""VLC/libVLC playback adapter."""

from __future__ import annotations

from pathlib import Path

from ani_watch.domain.errors import PlaybackError


class VlcPlayer:
    """Thin, testable wrapper around python-vlc."""

    def __init__(self, *, vlc_args: tuple[str, ...] = ()) -> None:
        try:
            import vlc
        except ImportError as exc:
            raise PlaybackError(
                "python-vlc is not installed. Recreate the Conda environment."
            ) from exc

        try:
            self._vlc = vlc
            self._instance = vlc.Instance(*vlc_args)
            self._player = self._instance.media_player_new()
        except Exception as exc:
            raise PlaybackError(
                "VLC could not be initialized. Install VLC/libVLC on the system."
            ) from exc

    def load(self, uri: str | Path) -> None:
        """Load a local path or URI into VLC."""
        try:
            media = self._instance.media_new(str(uri))
            self._player.set_media(media)
        except Exception as exc:
            raise PlaybackError(f"Unable to load media: {uri}") from exc

    def play(self) -> None:
        if self._player.play() == -1:
            raise PlaybackError("VLC failed to start playback.")

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def set_time(self, milliseconds: int) -> None:
        self._player.set_time(max(0, int(milliseconds)))

    def get_time(self) -> int:
        return int(self._player.get_time())

    def get_length(self) -> int:
        return int(self._player.get_length())

    def set_volume(self, volume: int) -> None:
        if self._player.audio_set_volume(max(0, min(int(volume), 200))) == -1:
            raise PlaybackError("VLC rejected the requested volume.")

    def is_playing(self) -> bool:
        return bool(self._player.is_playing())

    def is_complete(self) -> bool:
        """Return true when VLC has reached the end of the loaded media."""
        length = self.get_length()
        position = self.get_time()
        return length > 0 and position >= length and not self.is_playing()

    def state(self):
        return self._player.get_state()

    def audio_tracks(self) -> list[tuple[int, str]]:
        """Return VLC audio-track IDs and descriptions."""
        tracks = self._player.audio_get_track_description() or []
        return [(int(track_id), str(description)) for track_id, description in tracks]

    def select_audio_track(self, track_id: int) -> None:
        if self._player.audio_set_track(int(track_id)) == -1:
            raise PlaybackError(f"Unable to select audio track {track_id}.")

    def subtitle_tracks(self) -> list[tuple[int, str]]:
        """Return VLC subtitle-track IDs and descriptions."""
        tracks = self._player.video_get_spu_description() or []
        return [(int(track_id), str(description)) for track_id, description in tracks]

    def select_subtitle_track(self, track_id: int) -> None:
        if self._player.video_set_spu(int(track_id)) == -1:
            raise PlaybackError(f"Unable to select subtitle track {track_id}.")

    def release(self) -> None:
        """Release VLC resources."""
        self._player.release()
        self._instance.release()
