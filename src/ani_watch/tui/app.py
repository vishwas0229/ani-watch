"""Textual application shell for Ani-Watch."""

from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.widgets import Footer, Header, Static

from ani_watch import __version__


class AniWatchApp(App[None]):
    """Root terminal application."""

    TITLE = "Ani-Watch"
    SUB_TITLE = f"v{__version__}"

    CSS = """
    Screen {
        align: center middle;
    }

    #root {
        width: 80%;
        max-width: 100;
        height: auto;
        padding: 2 3;
    }

    #status {
        text-align: center;
        height: auto;
        margin: 1 0;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        """Build the initial application shell."""
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="root"):
                yield Static("Ani-Watch", id="status")
                yield Static(
                    "Foundation ready. Anime discovery, library, and playback "
                    "screens will be added incrementally."
                )
        yield Footer()

    def action_help(self) -> None:
        """Show the current shell help."""
        self.notify("Use q to quit. More shortcuts will arrive with the TUI screens.")
