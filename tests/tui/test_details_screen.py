from ani_watch.domain.details import AnimeDetails
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

        assert app.screen.query_one("#details-title").renderable == "Sample Anime"
        assert app.screen.query_one("#details-native-title").renderable == (
            "サンプルアニメ"
        )
        assert app.screen.query_one("#details-episodes-value").renderable == "24"
        assert app.screen.query_one("#details-score-value").renderable == "91.4/100"
        assert app.screen.query_one("#details-season-value").renderable == "FALL 2023"
        assert app.screen.query_one("#details-genres").renderable == (
            "Genres: Adventure, Drama, Fantasy"
        )


async def test_details_screen_empty_state_disables_metadata_actions() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen())
        await pilot.pause()

        assert app.screen.query_one("#details-title").renderable == "No anime selected"
        assert app.screen.query_one("#episodes").disabled
        assert app.screen.query_one("#favorite").disabled


async def test_favorite_action_toggles_local_state() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen(sample_anime()))
        await pilot.pause()

        favorite = app.screen.query_one("#favorite")
        assert favorite.label == "Favorite"

        await pilot.click("#favorite")
        assert favorite.label == "Unfavorite"
        assert "added to favorites locally" in str(
            app.screen.query_one("#details-status").renderable
        )

        await pilot.click("#favorite")
        assert favorite.label == "Favorite"
        assert "removed from favorites locally" in str(
            app.screen.query_one("#details-status").renderable
        )


async def test_details_screen_back_button_returns_home() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen(sample_anime()))
        await pilot.pause()

        await pilot.click("#back")
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
