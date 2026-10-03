from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.library import LibraryScreen
from ani_watch.tui.screens.player import PlayerScreen


async def test_library_screen_empty_state() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        await app.push_screen(LibraryScreen())
        await pilot.pause()

        assert app.screen.query_one("#library-heading").renderable == "YOUR LIBRARY"
        assert "Nothing currently in progress" in str(app.screen.query_one("#library-grid").renderable)


async def test_player_screen_without_manager_is_safe() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        await app.push_screen(PlayerScreen())
        await pilot.pause()

        await pilot.click("#play")
        await pilot.pause()

        assert "No playback manager" in str(app.screen.query_one("#player-status").renderable)
