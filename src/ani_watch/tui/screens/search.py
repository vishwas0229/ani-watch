"""Search screen for Ani-Watch."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from ani_watch.domain.errors import AniWatchError
from ani_watch.domain.models import AnimeRef
from ani_watch.metadata.anilist import AniListClient
from ani_watch.metadata.service import AnimeMetadataService
from ani_watch.tui.screens.details import AnimeDetailsScreen


class SearchScreen(Screen[None]):
    """Search AniList and open an anime's details."""

    CSS = """
    #search-page {
        width: 92%;
        max-width: 120;
        height: 100%;
        padding: 1 2;
        margin: 1 2;
    }
    #search-heading { text-style: bold; color: $accent; margin-bottom: 1; }
    #search-input { width: 1fr; }
    #search-submit { margin-left: 1; }
    #search-status { height: auto; margin: 1 0; color: $text-muted; }
    #search-results {
        height: 1fr; border: round $secondary; padding: 1;
    }
    .search-result { width: 1fr; margin-bottom: 1; }
    #back { margin-top: 1; }

    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("/", "focus_search", "Search"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._refs: dict[str, AnimeRef] = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="search-page"):
            yield Label("SEARCH ANIME", id="search-heading")
            with Horizontal():
                yield Input(placeholder="Enter an anime title…", id="search-input")
                yield Button("Search", id="search-submit", variant="primary")
            yield Static("Search the AniList catalog.", id="search-status")
            with VerticalScroll(id="search-results"):
                yield Static("No results yet. Enter a title above.", id="search-empty")
            yield Button("Back", id="back")

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        action = event.button.id
        if action == "search-submit":
            self.submit_search()
        elif action == "back":
            self.app.pop_screen()
        elif action in self._refs:
            self.open_details(self._refs[action])

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            self.submit_search()

    def submit_search(self) -> None:
        query = self.query_one("#search-input", Input).value.strip()
        if not query:
            self.query_one("#search-status", Static).update(
                "Enter an anime title to search."
            )
            return
        self.query_one("#search-status", Static).update(
            f'Searching AniList for "{query}"…'
        )
        self.run_worker(self._perform_search(query), exclusive=True)

    async def _perform_search(self, query: str) -> None:
        service = AnimeMetadataService(AniListClient())
        try:
            refs = await service.search(query)
        except AniWatchError as exc:
            self.query_one("#search-status", Static).update(str(exc))
            return
        except Exception:
            self.query_one("#search-status", Static).update(
                "Search failed. Check your network connection and try again."
            )
            return
        finally:
            await service.client.close()

        self._refs.clear()
        results = self.query_one("#search-results", VerticalScroll)
        await results.remove_children()

        if not refs:
            results.mount(Static("No anime found.", id="search-empty"))
            self.query_one("#search-status", Static).update("No results found.")
            return

        for index, ref in enumerate(refs):
            button_id = f"result-{index}"
            self._refs[button_id] = ref
            results.mount(
                Button(
                    ref.title,
                    id=button_id,
                    classes="search-result",
                )
            )
        self.query_one("#search-status", Static).update(
            f"Found {len(refs)} anime. Select one to open details."
        )

    def open_details(self, ref: AnimeRef) -> None:
        self.run_worker(self._load_details(ref), exclusive=True)

    async def _load_details(self, ref: AnimeRef) -> None:
        status = self.query_one("#search-status", Static)
        status.update(f"Loading details for {ref.title}…")
        client = AniListClient()
        service = AnimeMetadataService(client)
        try:
            anime = await service.details(ref.anilist_id)
        except AniWatchError as exc:
            status.update(str(exc))
            return
        except Exception:
            status.update("Unable to load anime details.")
            return
        finally:
            await client.close()
        self.app.push_screen(AnimeDetailsScreen(anime))

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_go_back(self) -> None:
        self.app.pop_screen()
