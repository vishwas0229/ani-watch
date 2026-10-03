"""Ani-Watch command-line interface."""

import typer

from ani_watch.config.runtime import CondaEnvironmentError, require_conda_environment

app = typer.Typer(
    name="ani-watch",
    help="Terminal-based anime discovery, tracking, and playback client.",
    no_args_is_help=False,
)


@app.command()
def doctor() -> None:
    """Check the local Ani-Watch installation."""
    typer.echo("Ani-Watch foundation is installed in a Conda environment.")


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """Launch Ani-Watch or run a subcommand."""
    try:
        require_conda_environment()
    except CondaEnvironmentError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if ctx.invoked_subcommand is None:
        from ani_watch.tui.app import AniWatchApp

        AniWatchApp().run()
