"""Anime details screen for Ani-Watch."""

from collections.abc import Iterable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ani_watch.domain.models import AnimeDetails


class AnimeDetailsScreen(Screen[None]):
    """Display provider-neutral metadata for one anime."""

    CSS = """
    #details-page {
        width: 92%;
        max-width: 120;
        height: 1fr;
        min-height: 0;
        overflow-y: auto;
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
        min-height: 3;
        max-height: 6;
        height: auto;
        overflow-y: auto;
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

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, anime: AnimeDetails | None = None) -> None:
        super().__init__()
        self.anime = anime
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
                yield Static(
                    "Waiting for an anime selection.",
                    id="details-status",
                )
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

    def _meta_row(
        self,
        label: str,
        value: str,
        widget_id: str,
    ) -> Iterable[Horizontal]:
        """Build one metadata label/value row."""
        with Horizontal(classes="detail-row"):
            yield Label(label, classes="detail-label")
            yield Static(value, classes="detail-value", id=widget_id)

    @staticmethod
    def _value(value: str | None, fallback: str = "Not available") -> str:
        """Return a human-readable fallback for missing text."""
        return value.strip() if value and value.strip() else fallback

    @staticmethod
    def _number(value: int | None) -> str:
        """Format an optional integer."""
        return str(value) if value is not None else "Not available"

    @staticmethod
    def _score(value: float | None) -> str:
        """Format an optional score without inventing one."""
        return f"{value:.1f}/100" if value is not None else "Not available"

    @staticmethod
    def _season(season: str | None, year: int | None) -> str:
        """Format season and year when available."""
        parts = [
            part
            for part in (season, str(year) if year is not None else None)
            if part
        ]
        return " ".join(parts) if parts else "Not available"

    @staticmethod
    def _genres(genres: tuple[str, ...]) -> str:
        """Format a genre list while keeping empty metadata explicit."""
        values = tuple(genre.strip() for genre in genres if genre.strip())
        return ", ".join(values) if values else "Not available"

    def _favorite_label(self) -> str:
        """Return the current local favorite action label."""
        return "Unfavorite" if self._favorite else "Favorite"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle details actions."""
        action = event.button.id

        if action == "back":
            self.app.pop_screen()
        elif action == "episodes":
            self.notify(
                "Episode selection will be connected in the Episode screen issue."
            )
        elif action == "favorite":
            self._favorite = not self._favorite
            event.button.label = self._favorite_label()
            state = "added to" if self._favorite else "removed from"
            self.query_one("#details-status", Static).update(
                f"Anime {state} favorites locally. Persistence will be added "
                "with the library/storage features."
            )

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()
