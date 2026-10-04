"""Watch history screen for Ani-Watch."""

from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ani_watch.domain.models import AnimeRef, EpisodeItem, WatchHistoryEntry
from ani_watch.services.library import LibraryService
from ani_watch.services.playback import PlaybackSession


class HistoryScreen(Screen[None]):
    """Display recent watch activity with playback handoff."""

    CSS = """
    #history-page {
        width: 92%;
        max-width: 120;
        height: 100%;
        padding: 1 2;
        margin: 0 2;
    }

    #history-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #history-summary {
        color: $text-muted;
        height: auto;
        margin-bottom: 1;
    }

    #history-list {
        height: 1fr;
        border: round $secondary;
        padding: 1;
    }

    .history-item {
        width: 1fr;
        margin-bottom: 1;
    }

    .history-item.selected {
        border: heavy $primary;
    }

    .history-title {
        text-style: bold;
    }

    .history-meta {
        color: $text-muted;
    }

    #history-status {
        height: auto;
        margin: 1 0;
        color: $text-muted;
    }

    #history-actions {
        height: auto;
        align-horizontal: center;
    }

    #history-actions Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("j", "next_entry", "Next"),
        ("k", "previous_entry", "Previous"),
        ("enter", "resume_selected", "Resume"),
    ]

    def __init__(
        self,
        entries: Sequence[WatchHistoryEntry] = (),
        *,
        library_service: LibraryService | None = None,
        playback_session: PlaybackSession | None = None,
    ) -> None:
        super().__init__()
        self.entries = tuple(entries)
        self.library_service = library_service
        self.playback_session = playback_session
        self._load_from_storage = not bool(entries)
        self._selected_index = 0
        self._playback_timer = None

    def compose(self) -> ComposeResult:
        """Render recent watch-history entries."""
        with Vertical(id="history-page"):
            yield Label("WATCH HISTORY", id="history-heading")
            yield Static(self._summary(), id="history-summary")

            with VerticalScroll(id="history-list"):
                if not self.entries:
                    yield Static(
                        "No watch history yet. Watched episodes will appear here "
                        "after playback tracking is connected.",
                        id="history-empty",
                    )
                else:
                    for index, entry in enumerate(self.entries):
                        yield Button(
                            self._entry_label(entry),
                            id=self._entry_id(index),
                            classes=self._entry_classes(index),
                        )

            yield Static(self._initial_status(), id="history-status")

            with Horizontal(id="history-actions"):
                yield Button(
                    "Resume",
                    id="resume",
                    variant="primary",
                    disabled=not bool(self.entries),
                )
                yield Button("Back", id="back")

    def on_mount(self) -> None:
        """Load persisted history when no explicit entries were supplied."""
        if self._load_from_storage:
            service = self.library_service
            if service is not None:
                self.library_service = service
                self.entries = tuple(service.recently_watched(50))
                self._rerender()
        self._focus_selected()


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle history selection and navigation actions."""
        action = event.button.id

        if action == "back":
            self.app.pop_screen()
            return
        if action == "resume":
            self.resume_selected()
            return
        if action and action.startswith("history-"):
            try:
                index = int(action.removeprefix("history-"))
            except ValueError:
                return
            self._select_index(index)

    def _rerender(self) -> None:
        """Synchronize the mounted history rows with persisted state."""
        history_list = self.query_one("#history-list", VerticalScroll)
        for child in list(history_list.children):
            child.remove()

        if not self.entries:
            history_list.mount(
                Static(
                    "No watch history yet. Watched episodes will appear here "
                    "after playback tracking is connected.",
                    id="history-empty",
                )
            )
        else:
            for index, entry in enumerate(self.entries):
                history_list.mount(
                    Button(
                        self._entry_label(entry),
                        id=self._entry_id(index),
                        classes=self._entry_classes(index),
                    )
                )

        self.query_one("#history-summary", Static).update(self._summary())
        self.query_one("#resume", Button).disabled = not bool(self.entries)
        self.query_one("#history-status", Static).update(self._initial_status())
        if self.entries:
            self._selected_index = min(self._selected_index, len(self.entries) - 1)
        else:
            self._selected_index = 0

    def _summary(self) -> str:
        """Return a compact history count."""
        count = len(self.entries)
        if not count:
            return "0 watched episodes"
        return f"{count} watched episode{'s' if count != 1 else ''}"

    def _initial_status(self) -> str:
        """Return the initial state shown below the history list."""
        if not self.entries:
            return "No persisted watch history yet."
        return "Select an entry and press Enter to resume from its saved position."

    @staticmethod
    def _entry_id(index: int) -> str:
        """Return a stable widget ID."""
        return f"history-{index}"

    @staticmethod
    def _entry_label(entry: WatchHistoryEntry) -> str:
        """Format one history entry for terminal display."""
        episode_title = (
            entry.episode_title.strip()
            if entry.episode_title
            else f"Episode {entry.episode_number}"
        )
        progress = HistoryScreen._progress_label(entry.progress_seconds, entry.duration_seconds)
        watched_at = (
            entry.watched_at.strftime("%Y-%m-%d %H:%M")
            if entry.watched_at is not None
            else "time unavailable"
        )
        return f"{entry.anime_title} • {episode_title} • {progress} • {watched_at}"

    @staticmethod
    def _progress_label(progress: int, duration: int | None) -> str:
        """Format saved playback progress."""
        if duration is None or duration <= 0:
            return "progress unavailable"
        bounded = max(0, min(progress, duration))
        percent = round((bounded / duration) * 100)
        return f"{percent}%"

    @staticmethod
    def _entry_classes(index: int) -> str:
        """Return display classes for a history row."""
        return "history-item selected" if index == 0 else "history-item"

    def _clear_selection(self) -> None:
        """Remove selection styling from every history row."""
        for button in self.query(".history-item.selected"):
            button.remove_class("selected")

    def _select_index(self, index: int) -> None:
        """Select a history entry and align focus."""
        if not self.entries or not 0 <= index < len(self.entries):
            return

        self._clear_selection()
        self._selected_index = index
        button = self.query_one(f"#{self._entry_id(index)}", Button)
        button.add_class("selected")
        button.focus()

        entry = self.entries[index]
        self.query_one("#history-status", Static).update(
            f"Selected {entry.anime_title} • Episode {entry.episode_number}."
        )

    def _focus_selected(self) -> None:
        """Focus the selected row when history exists."""
        if self.entries:
            self.query_one(f"#{self._entry_id(self._selected_index)}", Button).focus()

    def _move_selection(self, step: int) -> None:
        """Move within the history list and clamp at its edges."""
        if not self.entries:
            return
        candidate = max(0, min(self._selected_index + step, len(self.entries) - 1))
        self._select_index(candidate)

    def next_entry(self) -> None:
        """Select the next history entry."""
        self._move_selection(1)

    def previous_entry(self) -> None:
        """Select the previous history entry."""
        self._move_selection(-1)

    def _session(self) -> PlaybackSession:
        """Return the injected or application-owned playback session."""
        if self.playback_session is not None:
            return self.playback_session
        session = getattr(self.app, "playback_session", None)
        if session is None and hasattr(self.app, "get_playback_session"):
            session = self.app.get_playback_session()
        if session is None:
            raise RuntimeError("HistoryScreen requires a playback session.")
        self.playback_session = session
        return session

    def resume_selected(self) -> None:
        """Resolve the selected history entry and resume its saved position."""
        if not self.entries:
            self.query_one("#history-status", Static).update("There is no history entry to resume.")
            return
        if self.entries[self._selected_index].anime_id <= 0:
            self.query_one("#history-status", Static).update(
                "This history entry has no valid anime identifier."
            )
            return

        self.query_one("#history-status", Static).update("Resolving saved playback…")
        self.run_worker(self._resume_selected(), exclusive=True)

    async def _resume_selected(self) -> None:
        entry = self.entries[self._selected_index]
        duration_minutes = (
            max(1, round(entry.duration_seconds / 60))
            if entry.duration_seconds
            else None
        )
        episode = EpisodeItem(
            number=entry.episode_number,
            title=entry.episode_title,
            duration_minutes=duration_minutes,
            watched=True,
        )
        try:
            candidate = await self._session().start(
                AnimeRef(anilist_id=entry.anime_id, title=entry.anime_title),
                episode,
                episode_index=0,
                total_episodes=1,
            )
        except Exception as exc:
            self.query_one("#history-status", Static).update(
                f"Unable to resume Episode {entry.episode_number}: {exc}"
            )
            return

        self.query_one("#history-status", Static).update(
            f"Resumed {entry.anime_title} • Episode {entry.episode_number} "
            f"via {candidate.provider}."
        )
        if self._playback_timer is None:
            self._playback_timer = self.set_interval(1, self._save_progress)

    def _save_progress(self) -> None:
        if self.playback_session is not None and self.playback_session.active:
            self.playback_session.save_progress()

    def stop_playback(self) -> None:
        """Persist the resume position and stop playback before leaving."""
        if self._playback_timer is not None:
            self._playback_timer.pause()
            self._playback_timer = None
        if self.playback_session is not None:
            self.playback_session.stop()

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.stop_playback()
        self.app.pop_screen()

    def on_unmount(self) -> None:
        """Stop active playback when the history screen is removed."""
        self.stop_playback()

    def action_next_entry(self) -> None:
        """Handle j keyboard navigation."""
        self.next_entry()

    def action_previous_entry(self) -> None:
        """Handle k keyboard navigation."""
        self.previous_entry()

    def action_resume_selected(self) -> None:
        """Handle Enter resume handoff."""
        self.resume_selected()
