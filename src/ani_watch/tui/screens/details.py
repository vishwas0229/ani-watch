"""Anime details screen for Ani-Watch."""

from __future__ import annotations

from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ani_watch.domain.details import AnimeDetails
from ani_watch.metadata.factory import build_metadata_service
from ani_watch.tui.screens.episodes import EpisodeScreen


class AnimeDetailsScreen(Screen[None]):
    """Display provider-neutral metadata for one anime."""

    CSS = """
    #details-page {
        width: 92%;
        max-width: 120;
        height: 100%;
        padding: 1 2;
        margin: 0 2;
    }

    #details-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #details-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #details-native-title {
        color: $text-muted;
        margin-bottom: 1;
    }

    #details-meta {
        height: auto;
        padding: 1 2;
        border: round $secondary;
        margin-bottom: 1;
    }

    .detail-row {
        height: auto;
        margin-bottom: 1;
    }

    .detail-row:last-child {
        margin-bottom: 0;
    }

    .detail-label {
        width: 18;
        text-style: bold;
        color: $accent;
    }

    .detail-value {
        width: 1fr;
    }

    #details-description {
        min-height: 7;
        height: auto;
        padding: 1 2;
        border: round $secondary;
        margin-bottom: 1;
    }

    #details-genres {
        height: auto;
        margin-bottom: 1;
        color: $text-muted;
    }

    #details-status {
        height: auto;
        color: $text-muted;
        margin-bottom: 1;
    }

    #details-actions {
        height: auto;
        align-horizontal: center;
    }

    #details-actions Button {
        margin: 0 1;
    }
    """

    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(
        self,
        anime: AnimeDetails | None = None,
        service=None,
    ) -> None:
        super().__init__()
        self.anime = anime
        self.service = service
        self._favorite = anime.is_favorite if anime is not None else False

    def compose(self) -> ComposeResult:
        """Render the anime details surface and its actions."""
        with Vertical(id="details-page"):
            yield Label("ANIME DETAILS", id="details-heading")

            if self.anime is None:
                yield Label("No anime selected", id="details-title")
                yield Static(
                    "Open an anime from Search to view its metadata.",
                    id="details-native-title",
                )
                yield Static(
                    "Select an anime first. Provider-backed details will be "
                    "supplied through the metadata service.",
                    id="details-description",
                )
                yield Static("Genres: Not available", id="details-genres")
                yield Static("Waiting for an anime selection.", id="details-status")
            else:
                yield Label(self.anime.title, id="details-title")
                yield Static(
                    self._value(self.anime.native_title),
                    id="details-native-title",
                )

                with Vertical(id="details-meta"):
                    yield from self._meta_row(
                        "Status",
                        self._value(self.anime.status),
                        "details-status-value",
                    )
                    yield from self._meta_row(
                        "Format",
                        self._value(self.anime.format),
                        "details-format-value",
                    )
                    yield from self._meta_row(
                        "Episodes",
                        self._number(self.anime.episodes),
                        "details-episodes-value",
                    )
                    yield from self._meta_row(
                        "Score",
                        self._score(self.anime.score),
                        "details-score-value",
                    )
                    yield from self._meta_row(
                        "Season",
                        self._season(self.anime.season, self.anime.year),
                        "details-season-value",
                    )

                yield Static(
                    self._value(
                        self.anime.description,
                        fallback="No description available.",
                    ),
                    id="details-description",
                )
                yield Static(
                    f"Genres: {self._genres(self.anime.genres)}",
                    id="details-genres",
                )
                yield Static("Metadata loaded.", id="details-status")

            with Horizontal(id="details-actions"):
                yield Button(
                    "Episodes",
                    id="episodes",
                    variant="primary",
                    disabled=self.anime is None,
                )
                yield Button(
                    self._favorite_label(),
                    id="favorite",
                    disabled=self.anime is None,
                )
                yield Button("Back", id="back")

    def _meta_row(self, label: str, value: str, widget_id: str) -> ComposeResult:
        """Build one metadata label/value row."""
        with Horizontal(classes="detail-row"):
            yield Label(label, classes="detail-label")
            yield Static(value, classes="detail-value", id=widget_id)

    @staticmethod
    def _value(value: str | None, fallback: str = "Not available") -> str:
        return value.strip() if value and value.strip() else fallback

    @staticmethod
    def _number(value: int | None) -> str:
        return str(value) if value is not None else "Not available"

    @staticmethod
    def _score(value: float | None) -> str:
        return f"{value:.1f}/100" if value is not None else "Not available"

    @staticmethod
    def _season(season: str | None, year: int | None) -> str:
        parts = [
            part
            for part in (season, str(year) if year is not None else None)
            if part
        ]
        return " ".join(parts) if parts else "Not available"

    @staticmethod
    def _genres(genres: Sequence[str]) -> str:
        values = tuple(genre.strip() for genre in genres if genre.strip())
        return ", ".join(values) if values else "Not available"

    def _favorite_label(self) -> str:
        return "Unfavorite" if self._favorite else "Favorite"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle details actions."""
        action = event.button.id
        if action == "back":
            self.app.pop_screen()
        elif action == "favorite":
            self._favorite = not self._favorite
            event.button.label = self._favorite_label()
            state = "added to" if self._favorite else "removed from"
            self.query_one("#details-status", Static).update(
                f"Anime {state} favorites locally."
            )
        elif action == "episodes" and self.anime is not None:
            self.app.run_worker(
                self._open_episodes(),
                group="episode-metadata",
                exclusive=True,
                exit_on_error=False,
            )

    async def _open_episodes(self) -> None:
        service = self.service or build_metadata_service()
        try:
            episodes = await service.episodes(self.anime.anilist_id)
        except Exception as exc:
            self.query_one("#details-status", Static).update(
                f"Unable to load episode metadata: {exc}"
            )
            return

        self.app.push_screen(
            EpisodeScreen(
                self.anime.title,
                episodes,
                anime_id=self.anime.anilist_id,
            )
        )

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()
