"""VLC playback control screen for Ani-Watch."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from ani_watch.player.manager import PlaybackManager


class PlayerScreen(Screen[None]):
    """Expose playback lifecycle, track, and media-control actions."""

    CSS = """
    #player-page {
        width: 92%;
        max-width: 110;
        height: 100%;
        padding: 2;
        margin: 0 2;
    }

    #player-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #player-status {
        min-height: 4;
        border: round $secondary;
        padding: 1 2;
        margin-bottom: 1;
    }

    .control-row {
        height: auto;
        margin-bottom: 1;
    }

    .control-row Button {
        margin-right: 1;
    }

    #volume-input, #seek-input {
        width: 18;
        margin-right: 1;
    }

    .control-label {
        width: 16;
        padding: 1 0;
    }

    .control-select {
        width: 1fr;
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("space", "pause_resume", "Pause/Resume"),
        ("left", "seek_back", "−10s"),
        ("right", "seek_forward", "+10s"),
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, manager: PlaybackManager | None = None) -> None:
        super().__init__()
        self.manager = manager
        self._paused = False

    def compose(self) -> ComposeResult:
        with Vertical(id="player-page"):
            yield Label("PLAYER", id="player-heading")
            yield Static(
                "VLC playback controls are ready. Track selection and playback "
                "position are managed by the player adapter.",
                id="player-status",
            )
            with Horizontal(classes="control-row"):
                yield Button("Play", id="play", variant="primary")
                yield Button("Pause", id="pause")
                yield Button("Stop", id="stop")
                yield Button("−10s", id="seek-back")
                yield Button("+10s", id="seek-forward")
            with Horizontal(classes="control-row"):
                yield Input("80", id="volume-input")
                yield Button("Set Volume", id="volume")
            with Horizontal(classes="control-row"):
                yield Input("0", id="seek-input")
                yield Button("Seek", id="seek")
            with Horizontal(classes="control-row"):
                yield Label("Quality", classes="control-label")
                yield Select(
                    [("1080p", "1080p"), ("720p", "720p"), ("480p", "480p")],
                    value="1080p",
                    id="quality",
                    classes="control-select",
                )
                yield Button("Apply", id="quality-button")
            with Horizontal(classes="control-row"):
                yield Label("Audio", classes="control-label")
                yield Select(
                    [("Default", "default")],
                    value="default",
                    id="audio-track",
                    classes="control-select",
                    disabled=self.manager is None,
                )
                yield Button("Apply", id="audio-button", disabled=self.manager is None)
            with Horizontal(classes="control-row"):
                yield Label("Subtitles", classes="control-label")
                yield Select(
                    [("Default", "default")],
                    value="default",
                    id="subtitle-track",
                    classes="control-select",
                    disabled=self.manager is None,
                )
                yield Button(
                    "Apply",
                    id="subtitle-button",
                    disabled=self.manager is None,
                )
            yield Button("Back", id="back")

    def on_mount(self) -> None:
        """Populate available VLC tracks when a manager is attached."""
        if self.manager is None:
            return

        try:
            audio = [("Default", "default")]
            audio.extend(
                (label, str(track_id))
                for track_id, label in self.manager.player.audio_tracks()
            )
            subtitles = [("Default", "default")]
            subtitles.extend(
                (label, str(track_id))
                for track_id, label in self.manager.player.subtitle_tracks()
            )
            self.query_one("#audio-track", Select).set_options(audio)
            self.query_one("#subtitle-track", Select).set_options(subtitles)
        except Exception as exc:
            self._status(f"Track discovery unavailable: {exc}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle player controls."""
        action = event.button.id
        if action == "back":
            self.action_go_back()
            return
        if self.manager is None:
            self._status("No playback manager is attached.")
            return

        try:
            if action == "play":
                self.manager.resume()
                self._paused = False
            elif action == "pause":
                self.manager.pause()
                self._paused = True
            elif action == "stop":
                self.manager.stop()
            elif action == "seek-back":
                self.manager.seek_relative(-10)
            elif action == "seek-forward":
                self.manager.seek_relative(10)
            elif action == "volume":
                value = int(self.query_one("#volume-input", Input).value)
                self.manager.player.set_volume(value)
            elif action == "seek":
                value = int(self.query_one("#seek-input", Input).value)
                self.manager.player.seek(value)
            elif action == "quality-button":
                quality = str(self.query_one("#quality", Select).value)
                self.manager.player.set_quality(quality)
            elif action == "audio-button":
                track = str(self.query_one("#audio-track", Select).value)
                if track != "default":
                    self.manager.player.set_audio_track(int(track))
            elif action == "subtitle-button":
                track = str(self.query_one("#subtitle-track", Select).value)
                if track != "default":
                    self.manager.player.set_subtitle_track(int(track))
        except (TypeError, ValueError) as exc:
            self._status(f"Invalid player value: {exc}")
            return
        except Exception as exc:
            self._status(f"Player error: {exc}")
            return

        if action:
            self._status(f"Player action completed: {action}.")

    def _status(self, message: str) -> None:
        self.query_one("#player-status", Static).update(message)

    def action_pause_resume(self) -> None:
        if self.manager is None:
            self._status("No playback manager is attached.")
            return
        if self._paused:
            self.manager.resume()
        else:
            self.manager.pause()
        self._paused = not self._paused

    def action_seek_back(self) -> None:
        if self.manager:
            self.manager.seek_relative(-10)

    def action_seek_forward(self) -> None:
        if self.manager:
            self.manager.seek_relative(10)

    def action_go_back(self) -> None:
        self.app.pop_screen()
