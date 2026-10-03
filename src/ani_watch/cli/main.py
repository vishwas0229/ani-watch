"""Ani-Watch command-line interface."""

import typer

app = typer.Typer(
    name="ani-watch",
    help="Terminal-based anime discovery, tracking, and playback client.",
    no_args_is_help=False,
)


@app.command()
def doctor() -> None:
    """Check the local Ani-Watch installation."""
    typer.echo("Ani-Watch foundation is installed.")


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """Launch Ani-Watch or run a subcommand."""
    if ctx.invoked_subcommand is None:
        typer.echo("Ani-Watch v0.1.0")
        typer.echo("Foundation ready. TUI and playback modules will be added next.")
