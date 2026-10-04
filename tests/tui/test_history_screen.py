from datetime import UTC, datetime

from ani_watch.domain.models import WatchHistoryEntry
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.history import HistoryScreen


class FakePlaybackSession:
    active = False

    async def start(self, anime, episode, *, episode_index=0, total_episodes=1):
        self.active = True
        return MediaCandidate(uri="file:///episode.mp4", provider="fake")

    def save_progress(self) -> None:
        return

    def stop(self) -> None:
        self.active = False


def sample_history() -> tuple[WatchHistoryEntry, ...]:
    return (
        WatchHistoryEntry(
            anime_id=1,
            anime_title="Sample Anime",
            episode_number=5,
            episode_title="The Turning Point",
            watched_at=datetime(2026, 10, 3, 21, 30, tzinfo=UTC),
            progress_seconds=600,
            duration_seconds=1200,
        ),
        WatchHistoryEntry(
            anime_id=1,
            anime_title="Sample Anime",
            episode_number=4,
            progress_seconds=1200,
            duration_seconds=1200,
        ),
    )


async def test_history_screen_renders_entries() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(HistoryScreen(sample_history(), playback_session=FakePlaybackSession()))
        await pilot.pause()

        assert app.screen.query_one("#history-summary").content == ("2 watched episodes")
        assert "Sample Anime • The Turning Point • 50%" in str(
            app.screen.query_one("#history-0").label
        )
        assert "2026-10-03 21:30" in str(app.screen.query_one("#history-0").label)
        assert app.screen.query_one("#history-0").has_focus


async def test_history_selection_updates_status() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(HistoryScreen(sample_history()))
        await pilot.pause()

        await pilot.click("#history-1")
        await pilot.pause()

        assert "Selected Sample Anime • Episode 4" in str(
            app.screen.query_one("#history-status").content
        )
        assert app.screen.query_one("#history-1").has_class("selected")
        assert not app.screen.query_one("#history-0").has_class("selected")


async def test_history_resume_uses_provider_neutral_handoff() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(HistoryScreen(sample_history(), playback_session=FakePlaybackSession()))
        await pilot.pause()

        resume = app.screen.query_one("#resume")
        resume.focus()
        await pilot.press("enter")
        await pilot.pause()

        assert "Resumed Sample Anime" in str(app.screen.query_one("#history-status").content)


async def test_empty_history_disables_resume() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(HistoryScreen())
        await pilot.pause()

        assert app.screen.query_one("#history-empty")
        assert app.screen.query_one("#resume").disabled
        assert app.screen.query_one("#history-summary").content == ("0 watched episodes")


async def test_history_screen_back_and_escape() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(HistoryScreen(sample_history()))
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, HistoryScreen)
