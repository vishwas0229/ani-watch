from ani_watch.domain.models import EpisodeItem
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.episodes import EpisodeScreen


def sample_episodes() -> tuple[EpisodeItem, ...]:
    return (
        EpisodeItem(
            number=1,
            title="The Beginning",
            duration_minutes=24,
            watched=True,
        ),
        EpisodeItem(
            number=2,
            title="The Journey",
            duration_minutes=23,
        ),
        EpisodeItem(
            number=3,
            title="Unavailable Episode",
            available=False,
        ),
    )


async def test_episode_screen_renders_episode_list() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(
            EpisodeScreen("Sample Anime", sample_episodes())
        )
        await pilot.pause()

        assert app.screen.query_one("#anime-title").content == "Sample Anime"
        assert app.screen.query_one("#episode-summary").content == (
            "3 episodes • 1 watched"
        )
        assert "01 • The Beginning • 24m • Watched" in str(
            app.screen.query_one("#episode-0").label
        )
        assert "02 • The Journey • 23m" in str(
            app.screen.query_one("#episode-1").label
        )
        assert app.screen.query_one("#episode-2").disabled
        assert app.screen.query_one("#episode-0").has_focus


async def test_episode_selection_updates_status() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(EpisodeScreen("Sample Anime", sample_episodes()))
        await pilot.pause()

        await pilot.click("#episode-1")
        await pilot.pause()

        assert "Selected Episode 2: The Journey" in str(
            app.screen.query_one("#episode-status").content
        )
        assert app.screen.query_one("#episode-1").has_class("selected")
        assert not app.screen.query_one("#episode-0").has_class("selected")


async def test_episode_navigation_skips_unavailable_rows() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(EpisodeScreen("Sample Anime", sample_episodes()))
        await pilot.pause()

        await pilot.press("j")
        await pilot.pause()
        assert app.screen.query_one("#episode-1").has_focus

        await pilot.press("j")
        await pilot.pause()
        assert app.screen.query_one("#episode-1").has_focus


async def test_play_action_uses_provider_neutral_handoff() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(EpisodeScreen("Sample Anime", sample_episodes()))
        await pilot.pause()

        await pilot.press("space")
        await pilot.pause()

        assert "Playback requested for Episode 1" in str(
            app.screen.query_one("#episode-status").content
        )


async def test_empty_episode_screen_disables_play() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(EpisodeScreen("Sample Anime"))
        await pilot.pause()

        assert app.screen.query_one("#episodes-empty")
        assert app.screen.query_one("#play").disabled
        assert "0 episodes" in str(
            app.screen.query_one("#episode-summary").content
        )


async def test_episode_screen_back_button_returns_home() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(EpisodeScreen("Sample Anime", sample_episodes()))
        await pilot.pause()

        back = app.screen.query_one("#back", Button)
        back.focus()
        await pilot.press("enter")
        await pilot.pause()

        assert not isinstance(app.screen, EpisodeScreen)


async def test_episode_screen_escape_returns_home() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(EpisodeScreen("Sample Anime", sample_episodes()))
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(app.screen, EpisodeScreen)
