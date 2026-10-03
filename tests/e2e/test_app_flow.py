from ani_watch.tui.app import AniWatchApp


async def test_end_to_end_home_navigation() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("s")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "SettingsScreen"
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen is app.base_screen
        await pilot.press("f")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "FavoritesScreen"
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "HistoryScreen"
