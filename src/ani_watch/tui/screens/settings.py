"""Settings screen for Ani-Watch."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Input, Label, Select, Static

from ani_watch.config.settings import AppSettings
from ani_watch.config.store import SettingsStore


class SettingsScreen(Screen[None]):
    """Edit local application preferences."""

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
        margin-bottom: 1;
    }

    .setting-label {
        width: 22;
        text-style: bold;
    }

    .setting-control {
        width: 1fr;
    }

    #settings-status {
        height: auto;
        color: $text-muted;
        margin: 1 0;
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
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(
        self,
        settings: AppSettings | None = None,
        store: SettingsStore | None = None,
    ) -> None:
        super().__init__()
        self.store = store or SettingsStore()
        self.settings = settings or self.store.load()

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-page"):
            yield Label("SETTINGS", id="settings-heading")

            with Horizontal(classes="setting-row"):
                yield Label("Theme", classes="setting-label")
                yield Select(
                    options=[
                        ("Midnight", "midnight"),
                        ("Solarized", "solarized"),
                        ("Textual Dark", "textual-dark"),
                        ("Textual Light", "textual-light"),
                    ],
                    value=self.settings.ui.theme,
                    id="theme",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Episode layout", classes="setting-label")
                yield Select(
                    options=[
                        ("List", "list"),
                        ("Grid", "grid"),
                    ],
                    value=self.settings.ui.episode_layout,
                    id="layout",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Quality", classes="setting-label")
                yield Input(
                    value=self.settings.playback.quality,
                    placeholder="1080p",
                    id="quality",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Local playback first", classes="setting-label")
                yield Checkbox(
                    "Prefer configured local files",
                    value=self.settings.playback.local_first,
                    id="local-first",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Auto-next", classes="setting-label")
                yield Checkbox(
                    "Play next episode automatically",
                    value=self.settings.playback.auto_next,
                    id="auto-next",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Skip intro", classes="setting-label")
                yield Checkbox(
                    "Use configured intro skip",
                    value=self.settings.playback.skip_intro,
                    id="skip-intro",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Skip outro", classes="setting-label")
                yield Checkbox(
                    "Use configured outro skip",
                    value=self.settings.playback.skip_outro,
                    id="skip-outro",
                    classes="setting-control",
                )

            with Horizontal(classes="setting-row"):
                yield Label("Volume", classes="setting-label")
                yield Input(
                    value=str(self.settings.playback.volume),
                    placeholder="0-100",
                    id="volume",
                    classes="setting-control",
                )

            yield Static("Settings are stored in the user configuration directory.", id="settings-status")

            with Horizontal(id="settings-actions"):
                yield Button("Save", id="save", variant="primary")
                yield Button("Reset", id="reset")
                yield Button("Back", id="back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save, reset, and back."""
        if event.button.id == "save":
            self.save()
        elif event.button.id == "reset":
            self.settings = AppSettings()
            self.app.pop_screen()
            self.app.push_screen(SettingsScreen(self.settings, self.store))
        elif event.button.id == "back":
            self.action_go_back()

    def save(self) -> None:
        """Validate form values and persist settings."""
        try:
            volume = int(self.query_one("#volume", Input).value)
            settings = self.settings.model_copy(
                update={
                    "ui": self.settings.ui.model_copy(
                        update={
                            "theme": str(self.query_one("#theme", Select).value),
                            "episode_layout": str(self.query_one("#layout", Select).value),
                        }
                    ),
                    "playback": self.settings.playback.model_copy(
                        update={
                            "quality": self.query_one("#quality", Input).value.strip() or "1080p",
                            "local_first": self.query_one("#local-first", Checkbox).value,
                            "auto_next": self.query_one("#auto-next", Checkbox).value,
                            "skip_intro": self.query_one("#skip-intro", Checkbox).value,
                            "skip_outro": self.query_one("#skip-outro", Checkbox).value,
                            "volume": volume,
                        }
                    ),
                }
            )
            settings = AppSettings.model_validate(settings.model_dump())
            self.store.save(settings)
        except (TypeError, ValueError):
            self.query_one("#settings-status", Static).update(
                "Invalid settings. Volume must be an integer from 0 to 100."
            )
            return

        self.settings = settings
        theme = str(settings.ui.theme)
        if theme in self.app.available_themes:
            self.app.theme = theme
        self.query_one("#settings-status", Static).update("Settings saved.")

    def action_save(self) -> None:
        """Save with Ctrl+S."""
        self.save()

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()
