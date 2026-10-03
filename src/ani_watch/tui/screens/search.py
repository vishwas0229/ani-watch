"""Search screen for Ani-Watch."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static


class SearchScreen(Screen[None]):
    """Keyboard-friendly anime search surface."""

    CSS = """
    #search-page {
        width: 90%;
        max-width: 110;
        height: auto;
        padding: 2;
        margin: 1 2;
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
        min-height: 8;
        height: auto;
        border: round $secondary;
        padding: 1 2;
    }

    #back {
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("/", "focus_search", "Search"),
    ]

    def compose(self) -> ComposeResult:
        """Render the search controls and empty-state results area."""
        with Vertical(id="search-page"):
            yield Label("SEARCH ANIME", id="search-heading")
            with Horizontal():
                yield Input(
                    placeholder="Enter an anime title…",
                    id="search-input",
                )
                yield Button("Search", id="search-submit", variant="primary")
            yield Static(
                "Search is ready. Provider-backed results will be connected "
                "through the metadata service in the next phase.",
                id="search-status",
            )
            yield Static(
                "No results yet. Enter a title above.",
                id="search-results",
            )
            yield Button("Back", id="back")

    def on_mount(self) -> None:
        """Focus the search input when the screen opens."""
        self.query_one("#search-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle search and back actions."""
        if event.button.id == "search-submit":
            self.submit_search()
        elif event.button.id == "back":
            self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Submit a search when Enter is pressed in the input."""
        if event.input.id == "search-input":
            self.submit_search()

    def submit_search(self) -> None:
        """Validate the query and show the current search state."""
        query = self.query_one("#search-input", Input).value.strip()
        status = self.query_one("#search-status", Static)

        if not query:
            status.update("Enter an anime title to search.")
            return

        status.update(
            f'Search requested for "{query}". Metadata provider integration '
            "will populate results in the next phase."
        )

    def action_focus_search(self) -> None:
        """Focus the search input from the keyboard."""
        self.query_one("#search-input", Input).focus()

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()
