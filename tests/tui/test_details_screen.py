from ani_watch.domain.models import AnimeDetails
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.details import AnimeDetailsScreen


def sample_anime() -> AnimeDetails:
    return AnimeDetails(
        anilist_id=100,
        title="Sample Anime",
        native_title="サンプルアニメ",
        description="An example description for the details screen.",
        status="FINISHED",
        episodes=24,
        score=91.4,
        genres=("Adventure", "Drama", "Fantasy"),
        season="FALL",
        year=2023,
        format="TV",
    )


async def test_details_screen_renders_metadata() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen(sample_anime()))
        await pilot.pause()

        assert app.screen.query_one("#details-title").content == "Sample Anime"
        assert app.screen.query_one("#details-native-title").content == (
            "サンプルアニメ"
        )
        assert app.screen.query_one("#details-episodes-value").content == "24"
        assert app.screen.query_one("#details-score-value").content == "91.4/100"
        assert app.screen.query_one("#details-season-value").content == "FALL 2023"
        assert app.screen.query_one("#details-genres").content == (
            "Genres: Adventure, Drama, Fantasy"
        )


async def test_details_screen_empty_state_disables_metadata_actions() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen())
        await pilot.pause()

        assert app.screen.query_one("#details-title").content == "No anime selected"
        assert app.screen.query_one("#episodes").disabled
        assert app.screen.query_one("#favorite").disabled


async def test_favorite_action_toggles_local_state() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen(sample_anime()))
        await pilot.pause()

        favorite = app.screen.query_one("#favorite")
        assert str(favorite.label) == "Favorite"

        favorite.focus()
        await pilot.press("enter")
        assert str(favorite.label) == "Unfavorite"
        assert "added to favorites locally" in str(
            app.screen.query_one("#details-status").content
        )

        await pilot.click("#favorite")
        assert str(favorite.label) == "Favorite"
        assert "removed from favorites locally" in str(
            app.screen.query_one("#details-status").content
        )


async def test_details_screen_back_button_returns_home() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen(sample_anime()))
        await pilot.pause()

        back = app.screen.query_one("#back")
        back.focus()
        await pilot.press("enter")
        await pilot.pause()

        assert not isinstance(app.screen, AnimeDetailsScreen)


async def test_details_screen_escape_returns_home() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen(sample_anime()))
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(app.screen, AnimeDetailsScreen)
