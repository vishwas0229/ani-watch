import pytest

from ani_watch.domain.models import AnimeDetails
from ani_watch.domain.models import AnimeRef
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.details import AnimeDetailsScreen
from ani_watch.tui.screens.search import SearchScreen


class FakeMetadataService:
    def __init__(self, client) -> None:
        self.client = client

    async def search(self, query: str):
        return [AnimeRef(anilist_id=1, title=query.title())]

    async def details(self, anime_id: int):
        return AnimeDetails(
            anilist_id=anime_id,
            title="Sample Anime",
            description="Description",
            episodes=12,
            score=88.0,
        )


@pytest.fixture
def fake_service(monkeypatch):
    monkeypatch.setattr(
        "ani_watch.tui.screens.search.AnimeMetadataService",
        FakeMetadataService,
    )


async def test_home_search_button_opens_search_screen() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await pilot.click("#search")
        await pilot.pause()

        assert isinstance(app.screen, SearchScreen)
        assert app.screen.query_one("#search-input").has_focus


async def test_search_screen_validates_empty_query() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SearchScreen())
        await pilot.pause()

        await pilot.press("enter")
        status = app.screen.query_one("#search-status")

        assert "Enter an anime title" in str(status.renderable)


async def test_search_screen_renders_provider_results(fake_service) -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SearchScreen())
        await pilot.pause()

        search_input = app.screen.query_one("#search-input")
        search_input.value = "frieren"
        await pilot.press("enter")
        await pilot.pause()

        assert app.screen.query_one("#result-0").label == "Frieren"
        assert "Found 1 anime" in str(
            app.screen.query_one("#search-status").renderable
        )


async def test_search_result_opens_details(fake_service) -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SearchScreen())
        await pilot.pause()

        search_input = app.screen.query_one("#search-input")
        search_input.value = "frieren"
        await pilot.press("enter")
        await pilot.pause()

        await pilot.click("#result-0")
        await pilot.pause()

        assert isinstance(app.screen, AnimeDetailsScreen)
        assert app.screen.query_one("#details-title").renderable == "Sample Anime"


async def test_search_screen_back_button_returns_home() -> None:
    app = AniWatchApp()

    async with app.run_test() as pilot:
        await app.push_screen(SearchScreen())
        await pilot.pause()

        await pilot.click("#back")
        await pilot.pause()

        assert not isinstance(app.screen, SearchScreen)
