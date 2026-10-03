from tempfile import TemporaryDirectory
from pathlib import Path

from ani_watch.config.store import SettingsStore
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.settings import SettingsScreen


async def test_settings_screen_renders_controls() -> None:
    app = AniWatchApp()

    with TemporaryDirectory() as directory:
        store = SettingsStore(Path(directory) / "config.toml")
        async with app.run_test() as pilot:
            await app.push_screen(SettingsScreen(store=store))
            await pilot.pause()

            assert app.screen.query_one("#theme")
            assert app.screen.query_one("#density")
            assert app.screen.query_one("#quality")
            assert app.screen.query_one("#auto-next")
            assert app.screen.query_one("#save")

            await pilot.click("#save")
            await pilot.pause()

            assert "saved successfully" in str(
                app.screen.query_one("#settings-status").content
            )


async def test_settings_reset_restores_defaults() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen())
        await pilot.pause()

        await pilot.click("#reset")
        await pilot.pause()

        assert app.screen.query_one("#theme").value == "midnight"
        assert app.screen.query_one("#quality").value == "1080p"


async def test_settings_escape_returns() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen())
        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(app.screen, SettingsScreen)
