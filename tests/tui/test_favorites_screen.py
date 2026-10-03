from ani_watch.domain.models import FavoriteAnime
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.details import AnimeDetailsScreen
from ani_watch.tui.screens.favorites import FavoritesScreen


def sample_favorites() -> tuple[FavoriteAnime, ...]:
    return (
        FavoriteAnime(
            anime_id=1,
            title="Sample Anime",
            status="FINISHED",
            episodes=24,
            score=91.4,
            genres=("Drama", "Fantasy"),
        ),
        FavoriteAnime(
            anime_id=2,
            title="Another Anime",
            status="RELEASING",
            episodes=12,
        ),
    )


async def test_favorites_screen_renders_saved_anime() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(FavoritesScreen(sample_favorites()))
        await pilot.pause()

        assert app.screen.query_one("#favorites-summary").renderable == (
            "2 favorites"
        )
        assert "Sample Anime • FINISHED • 24 eps • 91.4/100" in str(
            app.screen.query_one("#favorite-0").label
        )
        assert app.screen.query_one("#favorite-0").has_focus


async def test_favorites_selection_updates_status() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(FavoritesScreen(sample_favorites()))
        await pilot.pause()

        await pilot.click("#favorite-1")
        await pilot.pause()

        assert app.screen.query_one("#favorite-1").has_class("selected")
        assert "Selected Another Anime" in str(
            app.screen.query_one("#favorites-status").renderable
        )


async def test_remove_favorite_updates_list_and_empty_state() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(FavoritesScreen(sample_favorites()))
        await pilot.pause()

        await pilot.click("#remove")
        await pilot.pause()

        assert len(app.screen.favorites) == 1
        assert app.screen.query_one("#favorites-summary").renderable == "1 favorite"
        assert not app.screen.query_one("#favorite-0").label.startswith("Sample Anime")

        await pilot.click("#remove")
        await pilot.pause()

        assert len(app.screen.favorites) == 0
        assert app.screen.query_one("#favorites-empty")
        assert app.screen.query_one("#remove").disabled
        assert app.screen.query_one("#details").disabled


async def test_empty_favorites_disables_actions() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(FavoritesScreen())
        await pilot.pause()

        assert app.screen.query_one("#favorites-empty")
        assert app.screen.query_one("#details").disabled
        assert app.screen.query_one("#remove").disabled


async def test_favorites_keyboard_navigation_and_open_details() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(FavoritesScreen(sample_favorites()))
        await pilot.pause()

        await pilot.press("j")
        await pilot.pause()
        assert app.screen.query_one("#favorite-1").has_focus

        await pilot.press("o")
        await pilot.pause()

        assert isinstance(app.screen, AnimeDetailsScreen)
        assert app.screen.query_one("#details-title").renderable == "Another Anime"
        assert app.screen.query_one("#details-episodes-value").renderable == "12"


async def test_favorites_screen_back_and_escape() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(FavoritesScreen(sample_favorites()))
        await pilot.pause()
        await pilot.click("#back")
        await pilot.pause()
        assert not isinstance(app.screen, FavoritesScreen)

        await app.push_screen(FavoritesScreen(sample_favorites()))
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, FavoritesScreen)
