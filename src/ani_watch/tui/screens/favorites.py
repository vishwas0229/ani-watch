"""Favorites screen for Ani-Watch."""

from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ani_watch.domain.models import AnimeDetails, FavoriteAnime
from ani_watch.tui.screens.details import AnimeDetailsScreen


class FavoritesScreen(Screen[None]):
    """Display saved anime favorites and local toggle actions."""

    CSS = """
    #favorites-page {
        width: 92%;
        max-width: 120;
        height: 100%;
        padding: 1 2;
        margin: 0 2;
    }

    #favorites-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #favorites-summary {
        color: $text-muted;
        height: auto;
        margin-bottom: 1;
    }

    #favorites-list {
        height: 1fr;
        border: round $secondary;
        padding: 1;
    }

    .favorite-item {
        width: 1fr;
        margin-bottom: 1;
    }

    .favorite-item.selected {
        border: heavy $primary;
    }

    #favorites-status {
        height: auto;
        margin: 1 0;
        color: $text-muted;
    }

    #favorites-actions {
        height: auto;
        align-horizontal: center;
    }

    #favorites-actions Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("j", "next_favorite", "Next"),
        ("k", "previous_favorite", "Previous"),
        ("delete", "remove_selected", "Remove"),
        ("o", "open_details", "Open"),
    ]

    def __init__(self, favorites: Sequence[FavoriteAnime] = ()) -> None:
        super().__init__()
        self.favorites = list(favorites)
        self._selected_index = 0

    def compose(self) -> ComposeResult:
        """Render the saved favorites list."""
        with Vertical(id="favorites-page"):
            yield Label("FAVORITES", id="favorites-heading")
            yield Static(self._summary(), id="favorites-summary")

            with VerticalScroll(id="favorites-list"):
                if not self.favorites:
                    yield Static(
                        "No favorites yet. Add an anime from its details screen "
                        "to build your library.",
                        id="favorites-empty",
                    )
                else:
                    for index, favorite in enumerate(self.favorites):
                        yield Button(
                            self._favorite_label(favorite),
                            id=self._favorite_id(index),
                            classes=self._favorite_classes(index),
                        )

            yield Static(self._initial_status(), id="favorites-status")

            with Horizontal(id="favorites-actions"):
                yield Button(
                    "Open Details",
                    id="details",
                    variant="primary",
                    disabled=not bool(self.favorites),
                )
                yield Button(
                    "Remove",
                    id="remove",
                    disabled=not bool(self.favorites),
                )
                yield Button("Back", id="back")

    def on_mount(self) -> None:
        """Focus the first favorite when the screen opens."""
        self._focus_selected()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle favorite selection, removal, and navigation."""
        action = event.button.id

        if action == "back":
            self.app.pop_screen()
            return
        if action == "remove":
            self.remove_selected()
            return
        if action == "details":
            self.open_details()
            return
        if action and action.startswith("favorite-"):
            try:
                index = int(action.removeprefix("favorite-"))
            except ValueError:
                return
            self._select_index(index)

    def _summary(self) -> str:
        """Return a compact favorite count."""
        count = len(self.favorites)
        return f"{count} favorite{'s' if count != 1 else ''}"

    def _initial_status(self) -> str:
        """Return the empty or ready state message."""
        if not self.favorites:
            return (
                "Favorites persistence will be connected in the "
                "library/storage phase."
            )
        return "Select an anime and press Enter, o, or Open Details to view it."

    @staticmethod
    def _favorite_id(index: int) -> str:
        """Return a stable widget ID."""
        return f"favorite-{index}"

    @staticmethod
    def _favorite_label(favorite: FavoriteAnime) -> str:
        """Format one favorite for terminal display."""
        meta = []
        if favorite.status:
            meta.append(favorite.status)
        if favorite.episodes is not None:
            meta.append(f"{favorite.episodes} eps")
        if favorite.score is not None:
            meta.append(f"{favorite.score:.1f}/100")
        suffix = f" • {' • '.join(meta)}" if meta else ""
        return f"{favorite.title}{suffix}"

    @staticmethod
    def _favorite_classes(index: int) -> str:
        """Return display classes for a favorite row."""
        return "favorite-item selected" if index == 0 else "favorite-item"

    def _select_index(self, index: int) -> None:
        """Select a favorite and align focus."""
        if not self.favorites or not 0 <= index < len(self.favorites):
            return

        for button in self.query(".favorite-item.selected"):
            button.remove_class("selected")

        self._selected_index = index
        button = self.query_one(f"#{self._favorite_id(index)}", Button)
        button.add_class("selected")
        button.focus()

        favorite = self.favorites[index]
        self.query_one("#favorites-status", Static).update(
            f"Selected {favorite.title}."
        )

    def _focus_selected(self) -> None:
        """Focus the currently selected favorite."""
        if self.favorites:
            self.query_one(f"#{self._favorite_id(self._selected_index)}", Button).focus()

    def _move_selection(self, step: int) -> None:
        """Move selection while keeping it inside the list."""
        if not self.favorites:
            return
        candidate = max(
            0, min(self._selected_index + step, len(self.favorites) - 1)
        )
        self._select_index(candidate)

    def next_favorite(self) -> None:
        """Select the next favorite."""
        self._move_selection(1)

    def previous_favorite(self) -> None:
        """Select the previous favorite."""
        self._move_selection(-1)

    def remove_selected(self) -> None:
        """Remove the selected favorite from this screen's local collection."""
        if not self.favorites:
            self.query_one("#favorites-status", Static).update(
                "There is no favorite to remove."
            )
            return

        removed = self.favorites.pop(self._selected_index)
        self._selected_index = max(
            0, min(self._selected_index, len(self.favorites) - 1)
        )

        favorites_list = self.query_one("#favorites-list", VerticalScroll)
        existing_buttons = list(favorites_list.query("Button.favorite-item"))

        for index, button in enumerate(existing_buttons):
            if index < len(self.favorites):
                favorite = self.favorites[index]
                button.label = self._favorite_label(favorite)
                button.display = True
                if index == self._selected_index:
                    button.add_class("selected")
                else:
                    button.remove_class("selected")
            else:
                button.display = False
                button.remove_class("selected")

        if self.favorites:
            self._focus_selected()
        elif not self.query("#favorites-empty"):
            favorites_list.mount(
                Static(
                    "No favorites yet. Add an anime from its details screen "
                    "to build your library.",
                    id="favorites-empty",
                )
            )

        self._refresh_action_state()
        self.query_one("#favorites-summary", Static).update(self._summary())
        self.query_one("#favorites-status", Static).update(
            f"Removed {removed.title} from favorites locally. "
            "Persistence will be added in the library/storage phase."
        )

    def _refresh_action_state(self) -> None:
        """Enable or disable favorite actions based on collection state."""
        self.query_one("#details", Button).disabled = not bool(self.favorites)
        self.query_one("#remove", Button).disabled = not bool(self.favorites)

    def open_details(self) -> None:
        """Open the selected favorite in the existing details screen."""
        if not self.favorites:
            self.query_one("#favorites-status", Static).update(
                "Select a favorite first."
            )
            return

        favorite = self.favorites[self._selected_index]
        self.app.push_screen(
            AnimeDetailsScreen(
                AnimeDetails(
                    anilist_id=favorite.anime_id,
                    title=favorite.title,
                    native_title=favorite.native_title,
                    status=favorite.status,
                    episodes=favorite.episodes,
                    score=favorite.score,
                    genres=favorite.genres,
                    is_favorite=True,
                )
            )
        )

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()

    def action_next_favorite(self) -> None:
        """Handle j keyboard navigation."""
        self.next_favorite()

    def action_previous_favorite(self) -> None:
        """Handle k keyboard navigation."""
        self.previous_favorite()

    def action_remove_selected(self) -> None:
        """Handle Delete keyboard shortcut."""
        self.remove_selected()

    def action_open_details(self) -> None:
        """Handle the o keyboard shortcut."""
        self.open_details()
