"""Ani-Watch command-line interface."""

import typer

from ani_watch.config.runtime import CondaEnvironmentError, require_conda_environment
from ani_watch.config.settings import AppSettings
from ani_watch.storage.database import Database
from ani_watch.storage.migrations import upgrade

app = typer.Typer(
    name="ani-watch",
    help="Terminal-based anime discovery, tracking, and playback client.",
    no_args_is_help=False,
)

db_app = typer.Typer(help="Database administration commands.")
app.add_typer(db_app, name="db")


@app.command()
def doctor() -> None:
    """Check the local Ani-Watch installation."""
    settings = AppSettings()
    typer.echo("Ani-Watch environment: Conda")
    typer.echo(f"Database: {settings.database_url}")
    typer.echo("VLC: available through python-vlc when the native VLC runtime is installed.")
    typer.echo("Redis: optional")


@db_app.command("upgrade")
def db_upgrade() -> None:
    """Create or upgrade the configured database schema."""
    settings = AppSettings()
    database = Database(settings.database_url)
    upgrade(database.engine)
    typer.echo("Database schema is up to date.")


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
