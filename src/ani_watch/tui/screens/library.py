"""Unified library dashboard for Ani-Watch."""

from __future__ import annotations

from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ani_watch.domain.favorite import FavoriteAnime
from ani_watch.domain.history import WatchHistoryEntry
from ani_watch.storage.db import Database
from ani_watch.storage.service import LibraryService


class LibraryScreen(Screen[None]):
    """Show continue watching, favorites, history, and statistics."""

    CSS = """
    #library-page {
        width: 96%;
        height: 100%;
        padding: 1 2;
        margin: 0 2;
    }

    #library-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #library-grid {
        height: 1fr;
    }

    .library-panel {
        width: 1fr;
        height: 1fr;
        border: round $secondary;
        padding: 1 2;
        margin: 0 1 1 0;
    }

    .library-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #library-status {
        height: auto;
        color: $text-muted;
        margin: 1 0;
    }

    #library-actions {
        height: auto;
        align-horizontal: center;
    }

    #library-actions Button {
        margin: 0 1;
    }

    @media (max-width: 90) {
        #library-grid {
            height: auto;
        }

        .library-panel {
            height: auto;
            min-height: 7;
        }
    }
    """

    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(
        self,
        history: Sequence[WatchHistoryEntry] = (),
        favorites: Sequence[FavoriteAnime] = (),
        service: LibraryService | None = None,
    ) -> None:
        super().__init__()
        self.history = tuple(history)
        self.favorites = tuple(favorites)
        self.service = service

    def compose(self) -> ComposeResult:
        with Vertical(id="library-page"):
            yield Label("YOUR LIBRARY", id="library-heading")
            with Horizontal(id="library-grid"):
                with Vertical(classes="library-panel"):
                    yield Label("Continue Watching", classes="library-title")
                    yield from self._continue_content()
                with Vertical(classes="library-panel"):
                    yield Label("Recently Watched", classes="library-title")
                    yield from self._history_content()
                with Vertical(classes="library-panel"):
                    yield Label("Favorites", classes="library-title")
                    yield from self._favorites_content()
                with Vertical(classes="library-panel"):
                    yield Label("Statistics", classes="library-title")
                    yield Static(self._statistics(), id="library-statistics")
            yield Static(
                "Loading local library data…",
                id="library-status",
            )
            with Horizontal(id="library-actions"):
                yield Button("Refresh", id="refresh")
                yield Button("Back", id="back")

    def on_mount(self) -> None:
        """Load persisted library data in a worker."""
        self.refresh()

    def refresh(self) -> None:
        """Refresh data from PostgreSQL without blocking the TUI."""
        self.app.run_worker(
            self._refresh_from_storage(),
            group="library",
            exclusive=True,
            exit_on_error=False,
        )

    async def _refresh_from_storage(self) -> None:
        """Read local library state and recompose the dashboard."""
        if self.service is None:
            try:
                from ani_watch.config.store import SettingsStore

                settings = SettingsStore().load()
                self.service = LibraryService(Database(settings.database))
            except Exception as exc:
                self.query_one("#library-status", Static).update(
                    f"Library configuration unavailable: {exc}"
                )
                return

        try:
            history = await self.app.run_in_thread(self.service.history)
        except AttributeError:
            try:
                history = self.service.history()
            except Exception as exc:
                self.query_one("#library-status", Static).update(
                    f"Library data unavailable: {exc}"
                )
                return
        except Exception as exc:
            self.query_one("#library-status", Static).update(
                f"Library data unavailable: {exc}"
            )
            return

        try:
            favorites = await self.app.run_in_thread(self.service.favorites)
        except AttributeError:
            try:
                favorites = self.service.favorites()
            except Exception as exc:
                self.query_one("#library-status", Static).update(
                    f"Library data unavailable: {exc}"
                )
                return
        except Exception as exc:
            self.query_one("#library-status", Static).update(
                f"Library data unavailable: {exc}"
            )
            return

        self.history = tuple(history)
        self.favorites = tuple(favorites)
        self.app.refresh(recompose=True)
        self.query_one("#library-status", Static).update(
            "Library refreshed from PostgreSQL."
        )

    def _continue_content(self) -> ComposeResult:
        for entry in self.history:
            if self._progress(entry) < 100:
                yield Static(
                    f"{entry.anime_title} • Episode {entry.episode_number} • "
                    f"{self._progress(entry)}%"
                )
                return
        yield Static("Nothing currently in progress.")

    def _history_content(self) -> ComposeResult:
        if not self.history:
            yield Static("No watched episodes yet.")
            return
        with VerticalScroll():
            for entry in self.history[:10]:
                yield Static(
                    f"{entry.anime_title} • Ep {entry.episode_number} • "
                    f"{self._progress(entry)}%"
                )

    def _favorites_content(self) -> ComposeResult:
        if not self.favorites:
            yield Static("No favorites saved yet.")
            return
        with VerticalScroll():
            for favorite in self.favorites[:10]:
                yield Static(favorite.title)

    def _statistics(self) -> str:
        total_seconds = sum(entry.progress_seconds for entry in self.history)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return (
            f"Favorites: {len(self.favorites)}\n"
            f"History entries: {len(self.history)}\n"
            f"Tracked watch time: {hours}h {minutes}m"
        )

    @staticmethod
    def _progress(entry: WatchHistoryEntry) -> int:
        if not entry.duration_seconds:
            return 0
        value = max(0, min(entry.progress_seconds, entry.duration_seconds))
        return round(value * 100 / entry.duration_seconds)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "refresh":
            self.refresh()

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()
