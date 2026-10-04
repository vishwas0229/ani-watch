"""Settings screen for Ani-Watch."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from ani_watch.auth.anilist import AniListTokenStore
from ani_watch.config.settings import AppSettings
from ani_watch.config.store import SettingsStore


class SettingsScreen(Screen[None]):
    """Edit user-facing Ani-Watch settings."""

    CSS = """
    #settings-page {
        width: 92%;
        max-width: 110;
        height: 100%;
        padding: 1 2;
        margin: 0 2;
    }

    #settings-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .setting-row {
        height: auto;
        padding: 1;
        margin-bottom: 1;
        border: round $secondary;
    }

    .setting-label {
        width: 26;
        text-style: bold;
    }

    .setting-control {
        width: 1fr;
    }

    #settings-status {
        height: auto;
        margin: 1 0;
        color: $text-muted;
    }

    #anilist-account {
        height: auto;
        padding: 1;
        border: round $secondary;
        margin-bottom: 1;
    }

    #settings-actions {
        height: auto;
        align-horizontal: center;
    }

    #settings-actions Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("ctrl+s", "save_settings", "Save"),
    ]

    def __init__(
        self,
        settings: AppSettings | None = None,
        store: SettingsStore | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or AppSettings()
        self.store = store or SettingsStore()

    def compose(self) -> ComposeResult:
        """Render editable settings with responsive layout."""
        with Vertical(id="settings-page"):
            yield Label("SETTINGS", id="settings-heading")

            with Horizontal(classes="setting-row"):
                yield Label("Theme", classes="setting-label")
                yield Select(
                    [
                        ("Midnight", "midnight"),
                        ("Mono", "mono"),
                        ("High Contrast", "high-contrast"),
                    ],
                    value=self.settings.ui.theme,
                    id="theme",
                    classes="setting-control",
                    allow_blank=False,
                )

            with Horizontal(classes="setting-row"):
                yield Label("Density", classes="setting-label")
                yield Select(
                    [("Compact", "compact"), ("Normal", "normal"), ("Comfortable", "comfortable")],
                    value=self.settings.ui.density,
                    id="density",
                    classes="setting-control",
                    allow_blank=False,
                )

            with Horizontal(classes="setting-row"):
                yield Label("Quality", classes="setting-label")
                yield Select(
                    [("1080p", "1080p"), ("720p", "720p"), ("480p", "480p"), ("Auto", "auto")],
                    value=self.settings.playback.quality,
                    id="quality",
                    classes="setting-control",
                    allow_blank=False,
                )

            with Horizontal(classes="setting-row"):
                yield Label("Auto-next episode", classes="setting-label")
                yield Select(
                    [("Enabled", "true"), ("Disabled", "false")],
                    value="true" if self.settings.playback.auto_next else "false",
                    id="auto-next",
                    classes="setting-control",
                    allow_blank=False,
                )

            with Horizontal(classes="setting-row"):
                yield Label("Local media", classes="setting-label")
                yield Input(
                    value=str(self.settings.local_media_root or ""),
                    placeholder="/path/to/your/anime/files",
                    id="local-media-root",
                    classes="setting-control",
                )

            yield Static(
                self._provider_status(),
                id="provider-status",
            )
            yield Static(
                self._account_status(),
                id="anilist-account",
            )
            yield Static(
                "Settings are stored locally. Use 'ani-watch auth login', "
                "'auth logout', 'auth status', or 'auth sync' for AniList account actions.",
                id="settings-status",
            )

            with Horizontal(id="settings-actions"):
                yield Button("Save", id="save", variant="primary")
                yield Button("Reset", id="reset")
                yield Button("Back", id="back")

    def on_mount(self) -> None:
        """Show the current provider and AniList configuration state."""
        self.query_one("#provider-status", Static).update(self._provider_status())
        self.query_one("#anilist-account", Static).update(self._account_status())

    def _provider_status(self) -> str:
        """Return actionable status for the configured playback provider."""
        root = self.settings.local_media_root
        if root is None:
            return (
                "Playback provider: not configured. Set Local media to a folder containing "
                "authorized/user-owned media."
            )
        try:
            root = root.expanduser()
            if root.is_dir():
                return f"Playback provider: local media ready • {root}"
            return (
                "Playback provider: local media path does not exist or is not a directory • "
                f"{root}"
            )
        except OSError:
            return f"Playback provider: unable to access local media path • {root}"

    @staticmethod
    def _account_status() -> str:
        """Return a token-presence status without exposing credentials."""
        try:
            authenticated = bool(AniListTokenStore().get())
        except Exception:
            return "AniList account: credential store unavailable."
        if authenticated:
            return "AniList account: signed in (token stored securely)."
        return "AniList account: not signed in."

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle settings actions."""
        if event.button.id == "save":
            self.save_settings()
        elif event.button.id == "reset":
            self.reset_settings()
        elif event.button.id == "back":
            self.app.pop_screen()

    def _selected(self, widget_id: str) -> str:
        """Read a selected value from a Select widget."""
        value = self.query_one(widget_id, Select).value
        return str(value)

    def save_settings(self) -> None:
        """Validate and persist the current controls."""
        self.settings.ui.theme = self._selected("#theme")
        self.settings.ui.density = self._selected("#density")
        self.settings.playback.quality = self._selected("#quality")
        self.settings.playback.auto_next = self._selected("#auto-next") == "true"

        raw_root = self.query_one("#local-media-root", Input).value.strip()
        if raw_root:
            root = Path(raw_root).expanduser()
            if not root.is_dir():
                self.query_one("#provider-status", Static).update(
                    f"Local media path does not exist or is not a directory: {root}"
                )
                return
            self.settings.local_media_root = root
        else:
            self.settings.local_media_root = None

        self.store.save(self.settings)
        app = self.app
        app.settings = self.settings
        if hasattr(app, "settings"):
            app.settings = self.settings
        if getattr(app, "provider_resolver", None) is not None:
            app.provider_resolver = None
        playback_session = getattr(app, "playback_session", None)
        if playback_session is not None and not playback_session.active:
            app.playback_session = None
        apply_theme = getattr(self.app, "apply_theme", None)
        if callable(apply_theme):
            apply_theme(self.settings.ui.theme)
        self.query_one("#provider-status", Static).update(self._provider_status())
        self.query_one("#settings-status", Static).update("Settings saved successfully.")

    def reset_settings(self) -> None:
        """Reset controls to typed defaults without network access."""
        self.settings = AppSettings()
        self.query_one("#theme", Select).value = self.settings.ui.theme
        self.query_one("#density", Select).value = self.settings.ui.density
        self.query_one("#quality", Select).value = self.settings.playback.quality
        self.query_one("#auto-next", Select).value = (
            "true" if self.settings.playback.auto_next else "false"
        )
        self.query_one("#local-media-root", Input).value = str(
            self.settings.local_media_root or ""
        )
        self.query_one("#provider-status", Static).update(self._provider_status())
        self.query_one("#settings-status", Static).update(
            "Settings reset. Press Save to persist the defaults."
        )

    def action_save_settings(self) -> None:
        """Handle Ctrl+S."""
        self.save_settings()

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()
