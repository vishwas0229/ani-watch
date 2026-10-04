"""Ani-Watch command-line interface."""

import asyncio

import typer

from ani_watch.auth.anilist import AniListAccountService
from ani_watch.auth.telegram import TelegramAccountService, TelegramCredentialStore
from ani_watch.config.runtime import CondaEnvironmentError, require_conda_environment
from ani_watch.config.settings import AppSettings
from ani_watch.config.store import SettingsStore
from ani_watch.domain.errors import AuthenticationError, ConfigurationError
from ani_watch.providers.telegram import TelegramMediaProvider
from ani_watch.services.anilist_sync import AniListSyncService
from ani_watch.services.library import LibraryService
from ani_watch.storage.database import Database
from ani_watch.storage.migrations import upgrade

app = typer.Typer(
    name="ani-watch",
    help="Terminal-based anime discovery, tracking, and playback client.",
    no_args_is_help=False,
)

db_app = typer.Typer(help="Database administration commands.")
auth_app = typer.Typer(help="AniList authentication and sync commands.")
telegram_app = typer.Typer(help="Telegram personal media commands.")
app.add_typer(db_app, name="db")
app.add_typer(auth_app, name="auth")
app.add_typer(telegram_app, name="telegram")


@app.command()
def doctor() -> None:
    """Check the local Ani-Watch installation."""
    settings = AppSettings()
    typer.echo("Ani-Watch environment: Conda")
    typer.echo(f"Database: {settings.database_url}")
    typer.echo("VLC: available through python-vlc when the native VLC runtime is installed.")
    typer.echo("Redis: optional")
    typer.echo(
        "Telegram: configured"
        if settings.telegram_api_id and settings.telegram_channel
        else "Telegram: not configured"
    )


@auth_app.command("login")
def auth_login(
    code: str | None = typer.Option(
        None,
        "--code",
        help="AniList authorization code or full callback URL.",
    ),
    client_id: str | None = typer.Option(None, "--client-id"),
    client_secret: str | None = typer.Option(
        None,
        "--client-secret",
        help="AniList client secret. Omit to enter it without echoing.",
    ),
    redirect_uri: str | None = typer.Option(None, "--redirect-uri"),
) -> None:
    """Authenticate with AniList and store the token in the OS credential store."""
    settings = AppSettings()
    account = AniListAccountService(settings)
    try:
        resolved_client_id = client_id or settings.anilist_client_id
        resolved_secret = client_secret or settings.anilist_client_secret
        resolved_redirect = redirect_uri or settings.anilist_redirect_uri

        if not resolved_client_id:
            resolved_client_id = typer.prompt("AniList client ID")
        if not resolved_secret:
            resolved_secret = typer.prompt("AniList client secret", hide_input=True)

        typer.echo("Open this AniList authorization URL in your browser:")
        typer.echo(
            account.authorization_url(
                client_id=resolved_client_id,
                redirect_uri=resolved_redirect,
            )
        )
        if not code:
            code = typer.prompt("Paste the authorization code or callback URL")

        asyncio.run(
            account.login(
                code,
                client_id=resolved_client_id,
                client_secret=resolved_secret,
                redirect_uri=resolved_redirect,
            )
        )
    except AuthenticationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    finally:
        asyncio.run(account.oauth.close())
    typer.echo("AniList login successful. Access token stored securely.")


@auth_app.command("logout")
def auth_logout() -> None:
    """Remove the stored AniList access token."""
    account = AniListAccountService(AppSettings())
    try:
        account.logout()
    except Exception as exc:
        typer.echo(f"Unable to clear AniList credentials: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo("AniList logout successful.")


@auth_app.command("status")
def auth_status() -> None:
    """Show AniList authentication state and account identity."""
    settings = AppSettings()
    account = AniListAccountService(settings)
    if not account.is_authenticated:
        typer.echo("AniList: not signed in.")
        return

    token = account.token()
    if not token:
        typer.echo("AniList: not signed in.")
        return

    sync = AniListSyncService(
        token,
        timeout=settings.network.timeout_seconds,
        retries=settings.network.retries,
    )
    try:
        viewer = asyncio.run(sync.viewer())
    except AuthenticationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    except Exception:
        typer.echo(
            "AniList: token is stored, but the account could not be reached. "
            "Check your network connection."
        )
        return
    finally:
        asyncio.run(sync.close())

    name = str(viewer.get("name") or "Unknown")
    user_id = viewer.get("id")
    typer.echo(f"AniList: signed in as {name} (ID {user_id}).")


@auth_app.command("sync")
def auth_sync(
    pull: bool = typer.Option(
        True,
        "--pull/--no-pull",
        help="Merge AniList watch progress into the local library.",
    ),
    push: bool = typer.Option(
        False,
        "--push",
        help="Push local watch progress to AniList.",
    ),
) -> None:
    """Synchronize watch progress with the authenticated AniList account."""
    if not pull and not push:
        typer.echo("Select at least one sync direction: --pull or --push.", err=True)
        raise typer.Exit(code=2)

    settings = AppSettings()
    token = AniListAccountService(settings).token()
    if not token:
        typer.echo("AniList: not signed in. Run 'ani-watch auth login' first.", err=True)
        raise typer.Exit(code=2)

    database = Database(settings.database_url)
    upgrade(database.engine)
    library = LibraryService(database)
    sync = AniListSyncService(
        token,
        timeout=settings.network.timeout_seconds,
        retries=settings.network.retries,
    )

    async def run_sync() -> tuple[int, int]:
        viewer = await sync.viewer()
        user_id = viewer.get("id")
        if not isinstance(user_id, int):
            raise AuthenticationError("AniList viewer ID is unavailable.")

        pulled = await sync.pull_into_library(library, user_id) if pull else 0
        pushed = await sync.push_library_progress(library) if push else 0
        return pulled, pushed

    try:
        pulled, pushed = asyncio.run(run_sync())
    except AuthenticationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        typer.echo(f"AniList sync failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    finally:
        asyncio.run(sync.close())
        database.dispose()

    if pull:
        typer.echo(f"Pulled {pulled} progress item(s) into the local library.")
    if push:
        typer.echo(f"Pushed {pushed} local media item(s) to AniList.")


@telegram_app.command("configure")
def telegram_configure(
    api_id: int | None = typer.Option(None, "--api-id", min=1),
    channel: str | None = typer.Option(None, "--channel"),
) -> None:
    """Configure Telegram API credentials and the authorized media channel."""
    settings = SettingsStore().load()
    resolved_api_id = api_id or settings.telegram_api_id
    resolved_channel = channel or settings.telegram_channel

    if resolved_api_id is None:
        resolved_api_id = typer.prompt("Telegram API ID", type=int)
    if resolved_channel is None:
        resolved_channel = typer.prompt("Telegram channel username or ID")

    api_hash = typer.prompt(
        "Telegram API hash",
        hide_input=True,
    )
    if not api_hash.strip():
        typer.echo("Telegram API hash cannot be empty.", err=True)
        raise typer.Exit(code=2)

    settings.telegram_api_id = resolved_api_id
    settings.telegram_channel = resolved_channel.strip()
    TelegramCredentialStore().save_api_hash(api_hash)
    SettingsStore().save(settings)

    typer.echo("Telegram configuration saved. API hash stored in the OS credential store.")
    typer.echo("Run 'ani-watch telegram login' to authorize the Telegram account.")


@telegram_app.command("login")
def telegram_login(
    phone: str | None = typer.Option(None, "--phone", help="Telegram phone number in international format."),
) -> None:
    """Authorize the local Telegram MTProto session."""
    settings = SettingsStore().load()
    account = TelegramAccountService(settings)
    try:
        asyncio.run(account.login(phone=phone))
    except AuthenticationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    finally:
        asyncio.run(account.close())
    typer.echo("Telegram login successful. Session stored locally and kept out of the repository.")


@telegram_app.command("status")
def telegram_status() -> None:
    """Check Telegram configuration and the local authorization session."""
    settings = SettingsStore().load()
    credentials = TelegramCredentialStore()
    configured = bool(
        settings.telegram_api_id
        and settings.telegram_channel
        and credentials.get_api_hash()
    )
    if not configured:
        typer.echo("Telegram: not configured. Run 'ani-watch telegram configure'.")
        return

    account = TelegramAccountService(settings, credential_store=credentials)
    try:
        authorized, identity = asyncio.run(account.status())
    except AuthenticationError:
        typer.echo("Telegram: configured but not authorized. Run 'ani-watch telegram login'.")
        return
    except Exception as exc:
        typer.echo(f"Telegram: unable to check account: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    finally:
        asyncio.run(account.close())

    typer.echo(f"Telegram: authorized as {identity or 'unknown account'}.")
    typer.echo(f"Channel: {settings.telegram_channel}")


@telegram_app.command("sync")
def telegram_sync(
    limit: int = typer.Option(100, "--limit", min=1, max=10000),
) -> None:
    """List authorized Telegram media visible to Ani-Watch."""
    settings = SettingsStore().load()
    provider = TelegramMediaProvider(settings)
    try:
        items = asyncio.run(provider.list_media(limit=limit))
    except Exception as exc:
        typer.echo(f"Telegram media scan failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    finally:
        asyncio.run(provider.close())

    if not items:
        typer.echo("No Telegram media found.")
        return

    for item in items:
        duration = item["duration_seconds"]
        duration_text = f", {duration}s" if duration is not None else ""
        typer.echo(
            f"message={item['message_id']} | {item['filename']} | "
            f"{item['size']} bytes{duration_text} | {item['mime_type']}"
        )


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

        try:
            AniWatchApp().run()
        except ConfigurationError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=2) from exc
