from textual.widgets import Button, Static

from ani_watch.domain.models import (
    ContinueWatchingItem,
    LibrarySnapshot,
    RecentlyWatchedItem,
)

from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.library import LibraryScreen


async def test_library_screen_renders_tracking_sections() -> None:
    snapshot = LibrarySnapshot(
        continue_watching=(
            ContinueWatchingItem(1, "Sample Anime", 6, 300, 1200),
        ),
        recently_watched=(
            RecentlyWatchedItem(1, "Sample Anime", 5),
        ),
        watched_episodes=5,
        favorites=2,
    )
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(LibraryScreen(snapshot))
        await pilot.pause()

        assert "5 watched" in str(app.screen.query_one("#library-summary").content)
        continue_button = app.screen.query_one("#continue-list Button", Button)
        assert "Sample Anime • Episode 6 • 25% complete" in str(continue_button.label)
        recent_item = app.screen.query_one("#recent-list Static", Static)
        assert recent_item.content == "Sample Anime • Episode 5"


async def test_library_empty_state() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(LibraryScreen())
        await pilot.pause()

        assert app.screen.query_one("#continue-empty")
        assert app.screen.query_one("#recent-empty")


async def test_library_back() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(LibraryScreen())
        back = app.screen.query_one("#back", Button)
        back.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, LibraryScreen)
