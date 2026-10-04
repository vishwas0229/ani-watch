from datetime import UTC, datetime

from ani_watch.domain.models import EpisodeItem, WatchHistoryEntry
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.history import HistoryScreen


class FakeMetadataService:
    async def episode_items(self, anime_id: int) -> list[EpisodeItem]:
        return [
            EpisodeItem(number=1, title="One"),
            EpisodeItem(number=2, title="Two"),
            EpisodeItem(number=3, title="Three"),
            EpisodeItem(number=4, title="Four"),
            EpisodeItem(number=5, title="Five"),
            EpisodeItem(number=6, title="Six"),
        ]


class FakePlaybackSession:
    active = False

    def __init__(self, *, completion: bool = False, next_index: int | None = None) -> None:
        self.completion = completion
        self.next_index = next_index
        self.starts: list[tuple[int, int, int]] = []

    async def start(self, anime, episode, *, episode_index=0, total_episodes=1):
        self.active = True
        self.starts.append((episode.number, episode_index, total_episodes))
        return MediaCandidate(uri="file:///episode.mp4", provider="fake")

    def tick(self) -> bool:
        completed = self.completion
        self.completion = False
        return completed

    def next_episode_index(self, total: int) -> int | None:
        return self.next_index

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
        await app.push_screen(
            HistoryScreen(
                sample_history(),
                playback_session=FakePlaybackSession(),
                metadata_service=FakeMetadataService(),
            )
        )
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
        session = FakePlaybackSession()
        await app.push_screen(
            HistoryScreen(
                sample_history(),
                playback_session=session,
                metadata_service=FakeMetadataService(),
            )
        )
        await pilot.pause()

        resume = app.screen.query_one("#resume")
        resume.focus()
        await pilot.press("enter")
        await pilot.pause()

        assert "Resumed Sample Anime" in str(app.screen.query_one("#history-status").content)
        assert session.starts == [(5, 4, 6)]


async def test_history_resume_preserves_full_episode_context_for_auto_next() -> None:
    session = FakePlaybackSession(completion=True, next_index=2)
    entries = (
        WatchHistoryEntry(
            anime_id=1,
            anime_title="Sample Anime",
            episode_number=2,
            episode_title="Two",
            progress_seconds=60,
            duration_seconds=120,
        ),
    )

    app = AniWatchApp()
    async with app.run_test() as pilot:
        await app.push_screen(
            HistoryScreen(
                entries,
                playback_session=session,
                metadata_service=FakeMetadataService(),
            )
        )
        await pilot.pause()

        await pilot.click("#resume")
        await pilot.pause()

        assert session.starts[0] == (2, 1, 6)

        app.screen._save_progress()
        await pilot.pause()

        assert session.starts[1] == (3, 2, 6)
        assert "Playing Episode 3" in str(app.screen.query_one("#history-status").content)


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
