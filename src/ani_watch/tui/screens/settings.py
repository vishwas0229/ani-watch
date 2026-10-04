"""Settings screen for Ani-Watch."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from ani_watch.auth.anilist import AniListTokenStore
from ani_watch.auth.telegram import TelegramCredentialStore
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
        telegram_hash_configured = self._telegram_hash_configured()
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
                    [
                        ("Compact", "compact"),
                        ("Normal", "normal"),
                        ("Comfortable", "comfortable"),
                    ],
                    value=self.settings.ui.density,
                    id="density",
                    classes="setting-control",
                    allow_blank=False,
                )

            with Horizontal(classes="setting-row"):
                yield Label("Quality", classes="setting-label")
                yield Select(
                    [
                        ("1080p", "1080p"),
                        ("720p", "720p"),
                        ("480p", "480p"),
                        ("Auto", "auto"),
                    ],
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

            with Horizontal(classes="setting-row"):
                yield Label("Streamlink URL", classes="setting-label")
                yield Input(
                    value=self.settings.streamlink_url_template or "",
                    placeholder="https://service.example/watch/{anime_id}/{episode}",
                    id="streamlink-url",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Direct media URL", classes="setting-label")
                yield Input(
                    value=self.settings.online_media_url_template or "",
                    placeholder="https://media.example/{anime_id}/{episode}.m3u8",
                    id="online-media-url",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Telegram API ID", classes="setting-label")
                yield Input(
                    value=str(self.settings.telegram_api_id or ""),
                    placeholder="12345678",
                    id="telegram-api-id",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Telegram API hash", classes="setting-label")
                yield Input(
                    placeholder="Stored securely in OS keyring"
                    if telegram_hash_configured
                    else "Paste api_hash here (masked)",
                    password=True,
                    id="telegram-api-hash",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Telegram channel", classes="setting-label")
                yield Input(
                    value=self.settings.telegram_channel or "",
                    placeholder="@username or -1001234567890",
                    id="telegram-channel",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Telegram scan limit", classes="setting-label")
                yield Input(
                    value=str(self.settings.telegram_scan_limit),
                    placeholder="1000",
                    id="telegram-scan-limit",
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
                "Telegram media is optional. Run 'ani-watch telegram login' once after "
                "configuring the API ID, API hash, and private channel. Telegram credentials "
                "are never stored in the repository.",
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
        """Return actionable status for the configured playback providers."""
        statuses: list[str] = []

        root = self.settings.local_media_root
        if root is not None:
            try:
                root = root.expanduser()
                if root.is_dir():
                    statuses.append(f"local media ready • {root}")
                else:
                    statuses.append(f"local media path unavailable • {root}")
            except OSError:
                statuses.append(f"local media path inaccessible • {root}")

        if self.settings.streamlink_url_template:
            statuses.append("Streamlink URL template configured")
        if self.settings.online_media_url_template:
            statuses.append("online direct-media template configured")

        if self.settings.telegram_api_id and self.settings.telegram_channel:
            if self._telegram_hash_configured():
                statuses.append("Telegram personal media configured")
            else:
                statuses.append("Telegram API hash missing")
        if not statuses:
            return (
                "Playback provider: not configured. Set Local media, Telegram personal media, "
                "Streamlink URL, or Direct media URL for an authorized source."
            )
        return "Playback providers: " + " • ".join(statuses)

    @staticmethod
    def _telegram_hash_configured() -> bool:
        try:
            return bool(TelegramCredentialStore().get_api_hash())
        except Exception:
            return False

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

        raw_streamlink = self.query_one("#streamlink-url", Input).value.strip()
        self.settings.streamlink_url_template = raw_streamlink or None

        raw_online = self.query_one("#online-media-url", Input).value.strip()
        self.settings.online_media_url_template = raw_online or None

        raw_api_id = self.query_one("#telegram-api-id", Input).value.strip()
        if raw_api_id:
            try:
                parsed_api_id = int(raw_api_id)
            except ValueError:
                self.query_one("#provider-status", Static).update(
                    "Telegram API ID must be a positive integer."
                )
                return
            if parsed_api_id <= 0:
                self.query_one("#provider-status", Static).update(
                    "Telegram API ID must be a positive integer."
                )
                return
            self.settings.telegram_api_id = parsed_api_id
        else:
            self.settings.telegram_api_id = None

        self.settings.telegram_channel = (
            self.query_one("#telegram-channel", Input).value.strip() or None
        )

        raw_scan_limit = self.query_one("#telegram-scan-limit", Input).value.strip()
        if raw_scan_limit:
            try:
                scan_limit = int(raw_scan_limit)
            except ValueError:
                self.query_one("#provider-status", Static).update(
                    "Telegram scan limit must be an integer between 1 and 10000."
                )
                return
            if not 1 <= scan_limit <= 10000:
                self.query_one("#provider-status", Static).update(
                    "Telegram scan limit must be between 1 and 10000."
                )
                return
            self.settings.telegram_scan_limit = scan_limit

        api_hash = self.query_one("#telegram-api-hash", Input).value.strip()
        if api_hash:
            try:
                TelegramCredentialStore().save_api_hash(api_hash)
            except Exception as exc:
                self.query_one("#provider-status", Static).update(
                    f"Unable to store Telegram API hash securely: {exc}"
                )
                return

        self.store.save(self.settings)
        app = self.app
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
        self.query_one("#settings-status", Static).update(
            "Settings saved successfully. "
            "Run 'ani-watch telegram login' once to authorize Telegram."
        )

    def reset_settings(self) -> None:
        """Reset controls to typed defaults without network access."""
        self.settings = AppSettings()
        self.query_one("#theme", Select).value = self.settings.ui.theme
        self.query_one("#density", Select).value = self.settings.ui.density
        self.query_one("#quality", Select).value = self.settings.playback.quality
        self.query_one("#auto-next", Select).value = (
            "true" if self.settings.playback.auto_next else "false"
        )
        self.query_one("#local-media-root", Input).value = str(self.settings.local_media_root or "")
        self.query_one("#streamlink-url", Input).value = self.settings.streamlink_url_template or ""
        self.query_one("#online-media-url", Input).value = (
            self.settings.online_media_url_template or ""
        )
        self.query_one("#telegram-api-id", Input).value = str(self.settings.telegram_api_id or "")
        self.query_one("#telegram-api-hash", Input).value = ""
        self.query_one("#telegram-channel", Input).value = self.settings.telegram_channel or ""
        self.query_one("#telegram-scan-limit", Input).value = str(self.settings.telegram_scan_limit)
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
