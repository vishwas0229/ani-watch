"""Library dashboard for tracking views."""

from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ani_watch.domain.models import (
    ContinueWatchingItem,
    LibrarySnapshot,
    RecentlyWatchedItem,
)


class LibraryScreen(Screen[None]):
    """Show continue-watching, recent activity and statistics."""

    CSS = """
    #library-page {
        width: 92%;
        height: 100%;
        padding: 1 2;
        margin: 0 2;
    }

    #library-heading { text-style: bold; color: $accent; margin-bottom: 1; }
    .library-panel {
        width: 1fr; height: 1fr; border: round $secondary;
        padding: 1 2; margin: 0 1 1 0;
    }
    .library-list { height: 1fr; }
    .library-item { width: 1fr; margin-bottom: 1; }
    #library-summary { color: $text-muted; height: auto; margin-bottom: 1; }
    #library-actions { height: auto; align-horizontal: center; }
    #library-actions Button { margin: 0 1; }

    """

    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(self, snapshot: LibrarySnapshot | None = None) -> None:
        super().__init__()
        self.snapshot = snapshot or LibrarySnapshot()

    def compose(self) -> ComposeResult:
        with Vertical(id="library-page"):
            yield Label("YOUR LIBRARY", id="library-heading")
            yield Static(self._summary(), id="library-summary")

            with Horizontal(id="library-columns"):
                with Vertical(classes="library-panel"):
                    yield Label("Continue Watching")
                    with VerticalScroll(classes="library-list", id="continue-list"):
                        if self.snapshot.continue_watching:
                            for item in self.snapshot.continue_watching:
                                yield Button(
                                    self._continue_label(item),
                                    classes="library-item",
                                )
                        else:
                            yield Static(
                                "Nothing in progress yet.",
                                id="continue-empty",
                            )

                with Vertical(classes="library-panel"):
                    yield Label("Recently Watched")
                    with VerticalScroll(classes="library-list", id="recent-list"):
                        if self.snapshot.recently_watched:
                            for item in self.snapshot.recently_watched:
                                yield Static(
                                    self._recent_label(item),
                                    classes="library-item",
                                )
                        else:
                            yield Static(
                                "No watch history yet.",
                                id="recent-empty",
                            )

            with Horizontal(id="library-actions"):
                yield Button("Refresh", id="refresh")
                yield Button("Back", id="back")

    def _summary(self) -> str:
        return (
            f"{self.snapshot.watched_episodes} watched • "
            f"{self.snapshot.favorites} favorites"
        )

    @staticmethod
    def _continue_label(item: ContinueWatchingItem) -> str:
        progress = "?"
        if item.duration_seconds and item.duration_seconds > 0:
            progress = f"{round(item.position_seconds / item.duration_seconds * 100)}%"
        return (
            f"{item.anime_title} • Episode {item.episode_number} • "
            f"{progress} complete"
        )

    @staticmethod
    def _recent_label(item: RecentlyWatchedItem) -> str:
        return f"{item.anime_title} • Episode {item.episode_number}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh":
            self.query_one("#library-summary", Static).update(self._summary())
        elif event.button.id == "back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
