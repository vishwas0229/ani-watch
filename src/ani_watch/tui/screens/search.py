"""Anime search screen backed by AniList metadata."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from ani_watch.metadata.client import AniListClient
from ani_watch.metadata.service import AniListMetadataService
from ani_watch.tui.screens.details import AnimeDetailsScreen


class SearchScreen(Screen[None]):
    """Keyboard-friendly anime search surface."""

    CSS = """
    #search-page {
        width: 92%;
        max-width: 120;
        height: 100%;
        padding: 1 2;
        margin: 0 2;
    }

    #search-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #search-input {
        width: 1fr;
    }

    #search-submit {
        margin-left: 1;
    }

    #search-status {
        height: auto;
        margin: 1 0;
        color: $text-muted;
    }

    #search-results {
        height: 1fr;
        min-height: 8;
        border: round $secondary;
        padding: 1 2;
    }

    .search-result {
        width: 1fr;
        margin-bottom: 1;
    }

    #back {
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("/", "focus_search", "Search"),
    ]

    def __init__(self, service: AniListMetadataService | None = None) -> None:
        super().__init__()
        self.service = service
        self._result_refs = ()

    def compose(self) -> ComposeResult:
        with Vertical(id="search-page"):
            yield Label("SEARCH ANIME", id="search-heading")
            with Horizontal():
                yield Input(
                    placeholder="Enter an anime title…",
                    id="search-input",
                )
                yield Button("Search", id="search-submit", variant="primary")
            yield Static("Ready to search the AniList catalog.", id="search-status")
            with VerticalScroll(id="search-results"):
                yield Static("No results yet. Enter a title above.", id="search-empty")
            yield Button("Back", id="back")

    def on_mount(self) -> None:
        """Focus the search input when the screen opens."""
        self.query_one("#search-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle search, result selection, and back actions."""
        action = event.button.id
        if action == "search-submit":
            self.submit_search()
        elif action == "back":
            self.app.pop_screen()
        elif action and action.startswith("result-"):
            self.open_result(action)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Submit a search when Enter is pressed in the input."""
        if event.input.id == "search-input":
            self.submit_search()

    def submit_search(self) -> None:
        """Validate the query and run the provider search in a worker."""
        query = self.query_one("#search-input", Input).value.strip()
        status = self.query_one("#search-status", Static)
        if not query:
            status.update("Enter an anime title to search.")
            return
        status.update(f'Searching for "{query}"…')
        self.app.run_worker(
            self._search(query),
            group="metadata",
            exclusive=True,
            exit_on_error=False,
        )

    async def _search(self, query: str) -> None:
        """Fetch search results without blocking the TUI."""
        service = self.service or self._default_service()
        status = self.query_one("#search-status", Static)
        results = self.query_one("#search-results", VerticalScroll)

        try:
            matches = await service.search(query)
        except Exception as exc:
            status.update(f"Search failed: {exc}")
            return

        results.remove_children()
        self._result_refs = tuple(matches)
        if not matches:
            results.mount(Static("No anime matches found.", id="search-empty"))
            status.update("No results found.")
            return

        for index, match in enumerate(matches):
            results.mount(
                Button(
                    match.title,
                    id=f"result-{index}",
                    classes="search-result",
                )
            )
        status.update(f"Found {len(matches)} result(s). Select one to view details.")

    def open_result(self, widget_id: str) -> None:
        """Open one search result in the details screen."""
        try:
            index = int(widget_id.removeprefix("result-"))
            anime_ref = self._result_refs[index]
        except (ValueError, IndexError):
            self.query_one("#search-status", Static).update(
                "The selected result is no longer available."
            )
            return

        self.app.run_worker(
            self._open_details(anime_ref.anilist_id),
            group="metadata-details",
            exclusive=True,
            exit_on_error=False,
        )

    async def _open_details(self, anime_id: int) -> None:
        service = self.service or self._default_service()
        try:
            details = await service.details(anime_id)
        except Exception as exc:
            self.query_one("#search-status", Static).update(
                f"Unable to load details: {exc}"
            )
            return
        self.app.push_screen(AnimeDetailsScreen(details))

    @staticmethod
    def _default_service() -> AniListMetadataService:
        """Build the metadata service from local configuration."""
        from ani_watch.auth.anilist import TokenStore
        from ani_watch.config.store import SettingsStore

        settings = SettingsStore().load()
        client = AniListClient(
            url=settings.anilist.graphql_url,
            access_token=TokenStore().load(),
            timeout=settings.providers.timeout_seconds,
        )
        return AniListMetadataService(client)

    def action_focus_search(self) -> None:
        """Focus the search input from the keyboard."""
        self.query_one("#search-input", Input).focus()

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()
