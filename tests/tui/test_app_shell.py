from pathlib import Path

from textual.widgets import Button, Label, Static

from ani_watch.config.settings import AppSettings
from ani_watch.domain.models import AnimeDetails
from ani_watch.metadata.cache import RedisCache
from ani_watch.services.library import LibraryService
from ani_watch.storage.database import Database
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.favorites import FavoritesScreen
from ani_watch.tui.screens.history import HistoryScreen


def test_app_shell_metadata() -> None:
    assert AniWatchApp.TITLE == "Ani-Watch"
    assert any(binding[0] == "q" for binding in AniWatchApp.BINDINGS)
    assert any(binding[0] == "r" for binding in AniWatchApp.BINDINGS)
    assert any(binding[0] == "f" for binding in AniWatchApp.BINDINGS)


def test_app_can_be_constructed() -> None:
    app = AniWatchApp()
    assert app.title == "Ani-Watch"


def test_app_uses_redis_cache_when_configured() -> None:
    app = AniWatchApp(settings=AppSettings(redis_url="redis://localhost:6379/0"))

    assert isinstance(app.metadata_service.cache, RedisCache)


async def test_home_screen_renders_primary_sections() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        assert app.query_one("#welcome-title", Label).content == "ANI-WATCH"
        assert app.query_one("#continue-watching", Static)
        assert app.query_one("#search", Button)
        assert app.query_one("#history", Button)
        assert app.query_one("#favorites", Button)
        assert app.query_one("#library", Button)
        assert app.query_one("#settings", Button)
        await pilot.pause()


async def test_home_history_button_opens_history_screen() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        button = app.query_one("#history", Button)
        button.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, HistoryScreen)


async def test_home_history_binding_opens_history_screen() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, HistoryScreen)


async def test_home_favorites_button_opens_favorites_screen() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        button = app.query_one("#favorites", Button)
        button.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, FavoritesScreen)


async def test_home_favorites_binding_opens_favorites_screen() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, FavoritesScreen)


async def test_keyboard_library_shortcuts_use_shared_persistence(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'shortcut.db'}")
    database.create_schema()
    library = LibraryService(database)

    library.anime.upsert(AnimeDetails(anilist_id=500, title="Shortcut Anime", episodes=2))
    library.favorite(500)
    library.save_progress(500, 1, 30, 120)

    app = AniWatchApp(
        settings=AppSettings(database_url=f"sqlite:///{tmp_path / 'shortcut.db'}"),
        library_service=library,
        database=database,
    )

    async with app.run_test() as pilot:
        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, FavoritesScreen)
        assert app.screen.query_one("#favorites-summary").content == "1 favorite"
        await pilot.press("escape")
        await pilot.pause()

        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, HistoryScreen)
        assert app.screen.query_one("#history-summary").content == "0 watched episodes"
        await pilot.press("escape")
        await pilot.pause()

        await pilot.press("l")
        await pilot.pause()
        assert app.screen.query_one("#library-summary").content == "0 watched • 1 favorites"

    database.dispose()


async def test_quit_button_exits_app() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()
        assert app.return_value is None
