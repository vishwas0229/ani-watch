from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.favorites import FavoritesScreen
from ani_watch.tui.screens.history import HistoryScreen
from ani_watch.tui.screens.library import LibraryScreen
from ani_watch.tui.screens.settings import SettingsScreen


async def test_tui_end_to_end_navigation() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await pilot.click("#history")
        await pilot.pause()
        assert isinstance(app.screen, HistoryScreen)
        await pilot.press("escape")
        await pilot.pause()

        await pilot.click("#favorites")
        await pilot.pause()
        assert isinstance(app.screen, FavoritesScreen)
        await pilot.press("escape")
        await pilot.pause()

        await pilot.click("#library")
        await pilot.pause()
        assert isinstance(app.screen, LibraryScreen)
        await pilot.press("escape")
        await pilot.pause()

        await pilot.click("#settings")
        await pilot.pause()
        assert isinstance(app.screen, SettingsScreen)
        await pilot.press("escape")
        await pilot.pause()
