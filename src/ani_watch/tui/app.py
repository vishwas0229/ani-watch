"""Textual application shell and primary navigation for Ani-Watch."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, Static

from ani_watch import __version__
from ani_watch.config.settings import AppSettings
from ani_watch.config.store import SettingsStore
from ani_watch.metadata.anilist import AniListClient
from ani_watch.metadata.cache import MemoryCache
from ani_watch.metadata.cached import CachedMetadataService
from ani_watch.tui.screens.favorites import FavoritesScreen
from ani_watch.tui.screens.history import HistoryScreen
from ani_watch.tui.screens.library import LibraryScreen
from ani_watch.tui.screens.search import SearchScreen
from ani_watch.tui.screens.settings import SettingsScreen


class AniWatchApp(App[None]):
    """Root terminal application."""

    TITLE = "Ani-Watch"
    SUB_TITLE = f"v{__version__}"

    CSS = """
    Screen { layout: vertical; }
    #welcome { height: auto; padding: 1 2; margin: 1 2; border: round $primary; }
    #welcome-title { text-style: bold; color: $accent; }
    #home-content { height: 1fr; padding: 0 2; }
    .section-title { text-style: bold; color: $accent; margin: 1 0; }
    #home-columns { height: 1fr; }
    .home-panel {
        width: 1fr;
        height: 1fr;
        border: round $secondary;
        padding: 1 2;
        margin: 0 1 1 0;
    }
    .home-copy { height: auto; margin-bottom: 1; }
    #home-actions {
        height: auto;
        padding: 0 2;
        margin-bottom: 1;
        align-horizontal: center;
    }
    #home-actions Button { margin: 0 1; }
    #home-status {
        height: auto;
        padding: 0 2;
        color: $text-muted;
    }
    .theme-mono Screen { background: #101010; color: #e8e8e8; }
    .theme-high-contrast Screen { background: #000000; color: #ffffff; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
        ("h", "show_home", "Home"),
        ("/", "show_search", "Search"),
        ("r", "show_history", "History"),
        ("f", "show_favorites", "Favorites"),
        ("l", "show_library", "Library"),
        ("s", "show_settings", "Settings"),
    ]

    def __init__(
        self,
        *,
        settings: AppSettings | None = None,
        metadata_service: CachedMetadataService | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or SettingsStore().load()
        self._owns_metadata_service = metadata_service is None
        self.metadata_service = metadata_service or CachedMetadataService(
            AniListClient(
                timeout=self.settings.network.timeout_seconds,
                retries=self.settings.network.retries,
            ),
            cache=MemoryCache(),
            offline=self.settings.network.offline_mode,
        )

    async def on_unmount(self) -> None:
        """Release resources owned by the application shell."""
        if self._owns_metadata_service:
            await self.metadata_service.close()

    def on_mount(self) -> None:
        self.apply_theme(self.settings.ui.theme)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="welcome"):
            yield Label("ANI-WATCH", id="welcome-title")
            yield Static(
                "Your anime corner in the terminal. Discover, track, and watch "
                "from one keyboard-friendly workspace."
            )
        with Vertical(id="home-content"):
            yield Label("HOME", classes="section-title")
            with Horizontal(id="home-columns"):
                with Vertical(classes="home-panel"):
                    yield Label("Continue Watching", classes="section-title")
                    yield Static(
                        "Your in-progress anime will appear here from local or "
                        "database-backed progress tracking.",
                        classes="home-copy",
                        id="continue-watching",
                    )
                with Vertical(classes="home-panel"):
                    yield Label("Discover", classes="section-title")
                    yield Static(
                        "Search AniList and inspect anime details or episodes.",
                        classes="home-copy",
                    )
                with Vertical(classes="home-panel"):
                    yield Label("Your Library", classes="section-title")
                    yield Static(
                        "Favorites, history, recent activity, and statistics "
                        "are available from the Library screen.",
                        classes="home-copy",
                    )
        with Horizontal(id="home-actions"):
            yield Button("Search", id="search", variant="primary")
            yield Button("History", id="history")
            yield Button("Favorites", id="favorites")
            yield Button("Library", id="library")
            yield Button("Settings", id="settings")
            yield Button("Quit", id="quit")
        yield Static(
            "Ready • Tab navigate • / search • r history • f favorites • "
            "l library • s settings • q quit",
            id="home-status",
        )
        yield Footer()

    def apply_theme(self, theme: str) -> None:
        """Apply the selected global theme class."""
        for name in ("midnight", "mono", "high-contrast"):
            self.remove_class(f"theme-{name}")
        self.add_class(f"theme-{theme}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle home dashboard navigation actions."""
        action = event.button.id
        if action == "quit":
            self.exit()
        elif action == "search":
            self.push_screen(SearchScreen(metadata_service=self.metadata_service))
        elif action == "history":
            self.push_screen(HistoryScreen())
        elif action == "favorites":
            self.push_screen(FavoritesScreen())
        elif action == "library":
            self.push_screen(LibraryScreen())
        elif action == "settings":
            self.push_screen(
                SettingsScreen(
                    settings=self.settings,
                    store=SettingsStore(),
                )
            )

    def action_show_search(self) -> None:
        """Open the anime search screen."""
        self.push_screen(SearchScreen(metadata_service=self.metadata_service))

    def action_show_history(self) -> None:
        """Open the watch history screen."""
        self.push_screen(HistoryScreen())

    def action_show_favorites(self) -> None:
        """Open the favorites screen."""
        self.push_screen(FavoritesScreen())

    def action_show_library(self) -> None:
        """Open the library screen."""
        self.push_screen(LibraryScreen())

    def action_show_settings(self) -> None:
        """Open the settings screen."""
        self.push_screen(
            SettingsScreen(
                settings=self.settings,
                store=SettingsStore(),
            )
        )

    def action_show_home(self) -> None:
        """Return to the home dashboard."""
        self.notify("You are already on Home.")

    def action_help(self) -> None:
        """Show the current keyboard shortcuts."""
        self.notify(
            "Tab: navigate • / Search • r History • f Favorites • l Library • s Settings • q Quit"
        )
