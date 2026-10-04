from pathlib import Path
from tempfile import TemporaryDirectory

from textual.widgets import Button

from ani_watch.auth.anilist import AniListTokenStore
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
            assert app.screen.query_one("#local-media-root")
            assert app.screen.query_one("#online-media-url")
            assert app.screen.query_one("#save")

            save = app.screen.query_one("#save", Button)
            save.focus()
            await pilot.press("enter")
            await pilot.pause()

            assert "saved successfully" in str(app.screen.query_one("#settings-status").content)


async def test_settings_reset_restores_defaults() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen())
        await pilot.pause()

        reset = app.screen.query_one("#reset", Button)
        reset.focus()
        await pilot.press("enter")
        await pilot.pause()

        assert app.screen.query_one("#theme").value == "midnight"
        assert app.screen.query_one("#quality").value == "1080p"
        assert app.screen.query_one("#online-media-url").value == ""


async def test_settings_escape_returns() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen())
        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(app.screen, SettingsScreen)


async def test_settings_screen_shows_anilist_account_state(monkeypatch) -> None:
    monkeypatch.setattr(AniListTokenStore, "get", lambda self: "stored-token")
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen())
        await pilot.pause()

        assert app.screen.query_one("#anilist-account").content == (
            "AniList account: signed in (token stored securely)."
        )


async def test_settings_save_local_media_root_updates_provider_state(tmp_path: Path) -> None:
    app = AniWatchApp()
    store = SettingsStore(tmp_path / "config.toml")

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen(store=store))
        await pilot.pause()

        root = app.screen.query_one("#local-media-root")
        root.value = str(tmp_path)
        await pilot.pause()

        save = app.screen.query_one("#save", Button)
        save.focus()
        await pilot.press("enter")
        await pilot.pause()

        assert app.settings.local_media_root == tmp_path
        assert "local media ready" in str(app.screen.query_one("#provider-status").content)
        assert app.provider_resolver is None


async def test_settings_save_online_media_template_updates_provider_state(tmp_path: Path) -> None:
    app = AniWatchApp()
    store = SettingsStore(tmp_path / "config.toml")

    async with app.run_test() as pilot:
        await app.push_screen(SettingsScreen(store=store))
        await pilot.pause()

        online = app.screen.query_one("#online-media-url")
        online.value = "https://media.example/{anime_id}/{episode}.m3u8"
        save = app.screen.query_one("#save", Button)
        save.focus()
        await pilot.press("enter")
        await pilot.pause()

        assert app.settings.online_media_url_template == (
            "https://media.example/{anime_id}/{episode}.m3u8"
        )
        assert "online direct-media template configured" in str(
            app.screen.query_one("#provider-status").content
        )
        assert app.provider_resolver is None
