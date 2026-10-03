"""Ani-Watch command-line interface."""

from __future__ import annotations

import os

import typer

from ani_watch.auth.anilist import AniListOAuth, TokenStore
from ani_watch.auth.sync import AniListSyncService
from ani_watch.config.runtime import CondaEnvironmentError, require_conda_environment
from ani_watch.config.store import SettingsStore
from ani_watch.metadata.client import AniListClient

app = typer.Typer(
    name="ani-watch",
    help="Conda-based terminal anime discovery, tracking, and playback client.",
    no_args_is_help=False,
)


def _settings():
    return SettingsStore().load()


def _metadata_client() -> AniListClient:
    settings = _settings()
    return AniListClient(
        url=settings.anilist.graphql_url,
        access_token=TokenStore().load(),
        timeout=settings.providers.timeout_seconds,
    )


def _require_client_credentials() -> tuple[str, str | None, str]:
    settings = _settings()
    client_id = os.getenv("ANILIST_CLIENT_ID") or settings.anilist.client_id
    secret = os.getenv("ANILIST_CLIENT_SECRET") or settings.anilist.client_secret
    redirect = os.getenv("ANILIST_REDIRECT_URI") or settings.anilist.redirect_uri

    if not client_id or not redirect:
        raise typer.BadParameter(
            "Set ANILIST_CLIENT_ID and ANILIST_REDIRECT_URI, or save them in settings."
        )
    return client_id, secret, redirect


@app.command()
def doctor() -> None:
    """Check the local Ani-Watch installation."""
    require_conda_environment()
    settings = _settings()
    typer.echo("Ani-Watch environment: Conda")
    typer.echo(f"Python package: {__package__ or 'ani_watch'}")
    typer.echo(f"Database: {settings.database.url}")
    typer.echo(f"Redis cache: {'enabled' if settings.cache.enabled else 'disabled'}")
    typer.echo(f"AniList token: {'configured' if TokenStore().load() else 'not configured'}")


@app.command()
def migrate() -> None:
    """Apply PostgreSQL schema migrations."""
    require_conda_environment()
    from alembic import command
    from alembic.config import Config

    settings = _settings()
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.database.url)
    command.upgrade(config, "head")
    typer.echo("Database migrations applied.")


@app.command()
def login(code: str | None = typer.Option(None, help="AniList authorization code.")) -> None:
    """Authenticate with AniList using the Authorization Code grant."""
    require_conda_environment()
    client_id, client_secret, redirect = _require_client_credentials()
    oauth = AniListOAuth(client_id, client_secret, redirect)

    if code is None:
        typer.echo("Open this AniList authorization URL in your browser:")
        typer.echo(oauth.authorization_url())
        code = typer.prompt("Paste the authorization code")

    import asyncio

    token = asyncio.run(oauth.exchange_code(code))
    TokenStore().save(token)
    typer.echo("AniList login successful; token saved locally.")


@app.command()
def logout() -> None:
    """Remove the locally stored AniList access token."""
    require_conda_environment()
    TokenStore().clear()
    typer.echo("AniList token removed.")


@app.command()
def search(query: str) -> None:
    """Search anime through AniList."""
    require_conda_environment()

    import asyncio

    async def run() -> None:
        from ani_watch.metadata.service import AniListMetadataService

        results = await AniListMetadataService(_metadata_client()).search(query)
        if not results:
            typer.echo("No matches found.")
            return
        for index, anime in enumerate(results, start=1):
            typer.echo(f"{index:02d}. {anime.title} [{anime.anilist_id}]")

    asyncio.run(run())


@app.command()
def sync() -> None:
    """Pull the authenticated AniList watch list."""
    require_conda_environment()

    import asyncio

    async def run() -> None:
        token = TokenStore().load()
        if not token:
            typer.echo("No AniList token configured. Run 'ani-watch login'.")
            return
        entries = await AniListSyncService(_metadata_client()).pull_watch_list()
        typer.echo(f"Fetched {len(entries)} AniList list entries.")

    asyncio.run(run())


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
