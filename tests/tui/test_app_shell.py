from textual.widgets import Button, Label, Static

from ani_watch.tui.app import AniWatchApp


def test_app_shell_metadata() -> None:
    assert AniWatchApp.TITLE == "Ani-Watch"
    assert any(binding[0] == "q" for binding in AniWatchApp.BINDINGS)


def test_app_can_be_constructed() -> None:
    app = AniWatchApp()
    assert app.title == "Ani-Watch"


async def test_home_screen_renders_primary_sections() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        assert app.query_one("#welcome-title", Label).renderable == "ANI-WATCH"
        assert app.query_one("#continue-watching", Static)
        assert app.query_one("#search", Button)
        assert app.query_one("#library", Button)
        assert app.query_one("#settings", Button)
        await pilot.pause()


async def test_quit_button_exits_app() -> None:
    app = AniWatchApp()
    async with app.run_test() as pilot:
        await pilot.click("#quit")
        await pilot.pause()
        assert app.return_value is None
