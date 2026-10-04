"""Episode selection screen for Ani-Watch."""

from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ani_watch.domain.errors import AniWatchError
from ani_watch.domain.models import AnimeRef, EpisodeItem
from ani_watch.services.playback import PlaybackSession


class EpisodeScreen(Screen[None]):
    """Keyboard-friendly episode browser with playback handoff."""

    CSS = """
    #episode-page {
        width: 92%;
        max-width: 120;
        height: 100%;
        padding: 1 2;
        margin: 0 2;
    }

    #episode-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #anime-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #episode-summary {
        color: $text-muted;
        height: auto;
        margin-bottom: 1;
    }

    #episodes-list {
        height: 1fr;
        border: round $secondary;
        padding: 1;
    }

    .episode-item {
        width: 1fr;
        margin-bottom: 1;
    }

    .episode-item.selected {
        border: heavy $primary;
    }

    .episode-item.watched {
        color: $text-muted;
    }

    .episode-item.unavailable {
        color: $error;
    }

    #episode-status {
        height: auto;
        margin: 1 0;
        color: $text-muted;
    }

    #episode-actions {
        height: auto;
        align-horizontal: center;
    }

    #episode-actions Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("j", "next_episode", "Next"),
        ("k", "previous_episode", "Previous"),
        ("space", "play_selected", "Play"),
    ]

    def __init__(
        self,
        anime_title: str,
        episodes: Sequence[EpisodeItem] = (),
        *,
        anime_id: int | None = None,
        playback_session: PlaybackSession | None = None,
    ) -> None:
        super().__init__()
        self.anime_title = anime_title.strip() or "Unknown anime"
        self.episodes = tuple(episodes)
        self.anime_id = anime_id
        self.playback_session = playback_session
        self._selected_index = 0
        self._playback_timer = None

    def compose(self) -> ComposeResult:
        """Render the episode list and navigation actions."""
        with Vertical(id="episode-page"):
            yield Label("EPISODES", id="episode-heading")
            yield Label(self.anime_title, id="anime-title")
            yield Static(self._summary(), id="episode-summary")

            with VerticalScroll(id="episodes-list"):
                if self.episodes:
                    for index, episode in enumerate(self.episodes):
                        yield Button(
                            self._episode_label(episode),
                            id=self._episode_id(index),
                            classes=self._episode_classes(index, episode),
                            disabled=not episode.available,
                        )
                else:
                    yield Static(
                        "No episode metadata available yet.",
                        id="episodes-empty",
                    )

            yield Static(self._initial_status(), id="episode-status")

            with Horizontal(id="episode-actions"):
                yield Button("Previous", id="previous")
                yield Button("Next", id="next")
                yield Button(
                    "Play",
                    id="play",
                    variant="primary",
                    disabled=not bool(self.episodes),
                )
                yield Button("Back", id="back")

    def on_mount(self) -> None:
        """Focus the first available episode when the screen opens."""
        self._focus_selected()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle episode selection and navigation actions."""
        action = event.button.id

        if action == "back":
            self.stop_playback()
            self.app.pop_screen()
            return
        if action == "play":
            self.play_selected()
            return
        if action == "previous":
            self.previous_episode()
            return
        if action == "next":
            self.next_episode()
            return
        if action and action.startswith("episode-"):
            try:
                index = int(action.removeprefix("episode-"))
            except ValueError:
                return
            self._select_index(index)

    def _summary(self) -> str:
        """Build a compact count of known and watched episodes."""
        total = len(self.episodes)
        watched = sum(episode.watched for episode in self.episodes)
        if not total:
            return "0 episodes • Waiting for metadata"
        return f"{total} episodes • {watched} watched"

    def _initial_status(self) -> str:
        """Return the initial state shown below the episode list."""
        if not self.episodes:
            return "Episode metadata will appear after the metadata integration."
        return "Select an episode with Tab or j/k, then press Space to play."

    @staticmethod
    def _episode_id(index: int) -> str:
        """Return a stable widget ID for one episode row."""
        return f"episode-{index}"

    @staticmethod
    def _episode_label(episode: EpisodeItem) -> str:
        """Format the visible episode row."""
        title = episode.title.strip() if episode.title else f"Episode {episode.number}"
        duration = f" • {episode.duration_minutes}m" if episode.duration_minutes is not None else ""
        state = " • Watched" if episode.watched else ""
        if not episode.available:
            state = " • Unavailable"
        return f"{episode.number:02d} • {title}{duration}{state}"

    @staticmethod
    def _episode_classes(index: int, episode: EpisodeItem) -> str:
        """Return display classes for an episode row."""
        classes = ["episode-item"]
        if index == 0:
            classes.append("selected")
        if episode.watched:
            classes.append("watched")
        if not episode.available:
            classes.append("unavailable")
        return " ".join(classes)

    def _select_index(self, index: int) -> None:
        """Select an episode and keep focus aligned with the selection."""
        if not self.episodes or not 0 <= index < len(self.episodes):
            return

        self._clear_selection_classes()
        self._selected_index = index
        button = self.query_one(f"#{self._episode_id(index)}", Button)
        button.add_class("selected")
        self._focus_selected()

        episode = self.episodes[index]
        state = "watched" if episode.watched else "unwatched"
        availability = "unavailable" if not episode.available else state
        self.query_one("#episode-status", Static).update(
            f"Selected Episode {episode.number}: {episode.title or 'Untitled'} ({availability})."
        )

    def _clear_selection_classes(self) -> None:
        """Remove the selected marker from all episode buttons."""
        for button in self.query(".episode-item.selected"):
            button.remove_class("selected")

    def _focus_selected(self) -> None:
        """Focus the selected episode button when it is available."""
        if not self.episodes:
            return
        button = self.query_one(f"#{self._episode_id(self._selected_index)}", Button)
        if not button.disabled:
            button.focus()

    def _move_selection(self, step: int) -> None:
        """Move selection without leaving the available episode range."""
        if not self.episodes:
            return

        candidate = self._selected_index + step
        candidate = max(0, min(candidate, len(self.episodes) - 1))

        if self.episodes[candidate].available:
            self._select_index(candidate)
            return

        direction = 1 if step >= 0 else -1
        while 0 <= candidate < len(self.episodes):
            if self.episodes[candidate].available:
                self._select_index(candidate)
                return
            candidate += direction

    def next_episode(self) -> None:
        """Select the next available episode."""
        self._move_selection(1)

    def previous_episode(self) -> None:
        """Select the previous available episode."""
        self._move_selection(-1)

    def _session(self) -> PlaybackSession:
        """Return the injected or application-owned playback session."""
        if self.playback_session is not None:
            return self.playback_session
        session = getattr(self.app, "playback_session", None)
        if session is None and hasattr(self.app, "get_playback_session"):
            session = self.app.get_playback_session()
        if session is None:
            raise RuntimeError("EpisodeScreen requires a playback session.")
        self.playback_session = session
        return session

    def play_selected(self) -> None:
        """Resolve the selected episode and start VLC playback asynchronously."""
        if not self.episodes:
            self.query_one("#episode-status", Static).update("No episode is available to play yet.")
            return

        episode = self.episodes[self._selected_index]
        if not episode.available:
            self.query_one("#episode-status", Static).update(
                f"Episode {episode.number} is unavailable."
            )
            return
        if self.anime_id is None:
            self.query_one("#episode-status", Static).update(
                "Playback is unavailable because the anime identifier is missing."
            )
            return

        self.query_one("#episode-status", Static).update(f"Resolving Episode {episode.number}…")
        self.run_worker(self._start_selected(), exclusive=True)

    async def _start_selected(self) -> None:
        """Resolve and start the selected episode through application services."""
        episode = self.episodes[self._selected_index]
        status = self.query_one("#episode-status", Static)
        try:
            candidate = await self._session().start(
                AnimeRef(anilist_id=self.anime_id, title=self.anime_title),
                episode,
                episode_index=self._selected_index,
                total_episodes=len(self.episodes),
            )
        except AniWatchError as exc:
            status.update(str(exc))
            return
        except Exception:
            status.update(
                f"Unable to start Episode {episode.number}. Check provider and VLC availability."
            )
            return

        if self._playback_timer is None:
            self._playback_timer = self.set_interval(1, self._poll_playback)
        status.update(
            f"Playing Episode {episode.number} via {candidate.provider}. "
            "Progress and resume are saved locally."
        )

    def _poll_playback(self) -> None:
        """Persist playback progress and trigger auto-next on completion."""
        session = self.playback_session
        if session is None:
            return

        try:
            completed = session.tick()
        except AniWatchError as exc:
            self.query_one("#episode-status", Static).update(str(exc))
            return
        except Exception:
            self.query_one(
                "#episode-status",
                Static,
            ).update(
                "Playback tracking failed. The episode can continue, "
                "but progress may not be saved."
            )
            return

        if not completed:
            return

        next_index = session.next_episode_index(len(self.episodes))
        while next_index is not None and not self.episodes[next_index].available:
            next_index += 1
            if next_index >= len(self.episodes):
                next_index = None

        if next_index is None:
            self.query_one("#episode-status", Static).update(
                f"Episode {self.episodes[self._selected_index].number} completed."
            )
            return

        self._select_index(next_index)
        self.query_one("#episode-status", Static).update(
            f"Episode completed. Starting Episode {self.episodes[next_index].number}…"
        )
        self.run_worker(self._start_selected(), exclusive=True)

    def stop_playback(self) -> None:
        """Persist the current playback position and stop VLC before leaving."""
        if self._playback_timer is not None:
            self._playback_timer.pause()
            self._playback_timer = None
        if self.playback_session is not None:
            self.playback_session.stop()

    def on_unmount(self) -> None:
        """Stop active playback when the episode screen is removed."""
        self.stop_playback()

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.stop_playback()
        self.app.pop_screen()

    def action_next_episode(self) -> None:
        """Handle j keyboard navigation."""
        self.next_episode()

    def action_previous_episode(self) -> None:
        """Handle k keyboard navigation."""
        self.previous_episode()

    def action_play_selected(self) -> None:
        """Handle Space playback handoff."""
        self.play_selected()
