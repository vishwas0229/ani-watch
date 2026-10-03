from textual.widgets import Input, Static

from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.search import SearchScreen


async def test_home_search_button_opens_search_screen() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await pilot.click("#search")
        await pilot.pause()

        assert isinstance(app.screen, SearchScreen)
        assert app.screen.query_one("#search-input", Input).has_focus


async def test_search_screen_validates_empty_query() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SearchScreen())
        await pilot.pause()

        await pilot.press("enter")
        status = app.screen.query_one("#search-status", Static)

        assert "Enter an anime title" in str(status.renderable)


async def test_search_screen_accepts_query() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SearchScreen())
        await pilot.pause()

        search_input = app.screen.query_one("#search-input", Input)
        search_input.value = "Frieren"
        await pilot.press("enter")
        await pilot.pause()

        status = app.screen.query_one("#search-status", Static)
        assert 'Search requested for "Frieren"' in str(status.renderable)


async def test_search_screen_back_button_returns_home() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SearchScreen())
        await pilot.pause()

        await pilot.click("#back")
        await pilot.pause()

        assert not isinstance(app.screen, SearchScreen)
