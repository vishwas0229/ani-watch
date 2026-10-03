from pathlib import Path

from ani_watch.config.settings import AppSettings
from ani_watch.config.store import SettingsStore
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.settings import SettingsScreen


async def test_settings_screen_saves_preferences(tmp_path: Path) -> None:
    app = AniWatchApp()
    store = SettingsStore(tmp_path / "config.toml")

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen(AppSettings(), store))
        await pilot.pause()

        app.screen.query_one("#quality").value = "720p"
        app.screen.query_one("#volume").value = "60"
        await pilot.click("#save")
        await pilot.pause()

        saved = store.load()
        assert saved.playback.quality == "720p"
        assert saved.playback.volume == 60


async def test_settings_screen_rejects_invalid_volume(tmp_path: Path) -> None:
    app = AniWatchApp()
    store = SettingsStore(tmp_path / "config.toml")

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen(AppSettings(), store))
        await pilot.pause()

        app.screen.query_one("#volume").value = "loud"
        await pilot.click("#save")
        await pilot.pause()

        assert "Volume must be an integer" in str(
            app.screen.query_one("#settings-status").renderable
        )
