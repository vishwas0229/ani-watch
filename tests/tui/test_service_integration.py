from pathlib import Path

from ani_watch.config.settings import AppSettings
from ani_watch.domain.models import AnimeDetails, EpisodeItem
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.providers.registry import ProviderRegistry
from ani_watch.providers.resilience import ProviderResolver
from ani_watch.services.library import LibraryService
from ani_watch.services.playback import PlaybackManager, PlaybackSession
from ani_watch.storage.database import Database
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.episodes import EpisodeScreen
from ani_watch.tui.screens.favorites import FavoritesScreen
from ani_watch.tui.screens.history import HistoryScreen
from ani_watch.tui.screens.library import LibraryScreen
from ani_watch.tui.screens.details import AnimeDetailsScreen


class FakeMetadataService:
    async def episode_items(self, anime_id: int) -> list[EpisodeItem]:
        assert anime_id == 100
        return [
            EpisodeItem(number=1, title="One", duration_minutes=2),
            EpisodeItem(number=2, title="Two", duration_minutes=2),
        ]

    async def search(self, query: str):
        return []

    async def details(self, anime_id: int):
        return AnimeDetails(anilist_id=anime_id, title="Sample Anime", episodes=2)


class FakePlayer:
    def __init__(self) -> None:
        self.loaded: list[str] = []
        self.position = 0
        self.duration = 120_000
        self.volume = 0
        self.playing = False

    def load(self, uri: str) -> None:
        self.loaded.append(uri)
        self.position = 0

    def play(self) -> None:
        self.playing = True

    def pause(self) -> None:
        self.playing = False

    def stop(self) -> None:
        self.playing = False

    def set_time(self, milliseconds: int) -> None:
        self.position = milliseconds

    def get_time(self) -> int:
        return self.position

    def get_length(self) -> int:
        return self.duration

    def set_volume(self, volume: int) -> None:
        self.volume = volume

    def is_playing(self) -> bool:
        return self.playing

    def is_complete(self) -> bool:
        return self.position >= self.duration and not self.playing


class FakeProvider:
    name = "fake"

    async def available(self, anime, episode) -> bool:
        return True

    async def resolve(self, anime, episode, *, quality=None) -> MediaCandidate:
        return MediaCandidate(
            uri=f"file:///anime-{anime.anilist_id}-episode-{episode.number}.mp4",
            provider=self.name,
            quality=quality,
        )


def build_app(tmp_path: Path) -> tuple[AniWatchApp, Database, FakePlayer]:
    database = Database(f"sqlite:///{tmp_path / 'ani-watch.db'}")
    database.create_schema()
    library = LibraryService(database)
    player = FakePlayer()
    manager = PlaybackManager(player, AppSettings().playback)
    resolver = ProviderResolver(ProviderRegistry([FakeProvider()]))
    session = PlaybackSession(manager, resolver, library)
    library.anime.upsert(
        AnimeDetails(
            anilist_id=100,
            title="Sample Anime",
            episodes=2,
        )
    )
    return (
        AniWatchApp(
            settings=AppSettings(database_url=f"sqlite:///{tmp_path / 'ani-watch.db'}"),
            metadata_service=FakeMetadataService(),
            library_service=library,
            provider_resolver=resolver,
            playback_session=session,
            database=database,
        ),
        database,
        player,
    )


async def test_details_to_episodes_to_playback_persists_progress_and_auto_next(tmp_path: Path) -> None:
    app, database, player = build_app(tmp_path)
    library = app.library_service
    assert library is not None
    library.progress.save(100, 1, 30, 120)

    async with app.run_test() as pilot:
        await app.push_screen(AnimeDetailsScreen(
            AnimeDetails(anilist_id=100, title="Sample Anime", episodes=2),
            metadata_service=app.metadata_service,
            library_service=library,
        ))
        await pilot.pause()

        await pilot.click("#favorite")
        assert library.favorites.list() == [100]

        await pilot.click("#episodes")
        await pilot.pause()

        assert isinstance(app.screen, EpisodeScreen)
        assert app.screen.query_one("#episode-0").label.startswith("01 • One")

        await pilot.click("#play")
        await pilot.pause()

        assert player.loaded[-1].endswith("episode-1.mp4")
        assert player.position == 30_000
        assert player.playing is True

        player.position = player.duration
        player.playing = False
        app.screen._poll_playback()
        await pilot.pause()

        history = library.recently_watched(10)
        assert len(history) == 1
        assert history[0].episode_number == 1
        assert app.screen.query_one("#episode-1").has_class("selected")
        assert player.loaded[-1].endswith("episode-2.mp4")

    database.dispose()


async def test_history_favorites_and_library_read_persisted_state(tmp_path: Path) -> None:
    app, database, player = build_app(tmp_path)
    library = app.library_service
    assert library is not None
    library.favorite(100)
    library.progress.save(100, 2, 60, 120)

    async with app.run_test() as pilot:
        await app.push_screen(FavoritesScreen(library_service=library))
        await pilot.pause()
        assert app.screen.query_one("#favorites-summary").content == "1 favorite"

        await app.push_screen(HistoryScreen(library_service=library))
        await pilot.pause()
        assert app.screen.query_one("#history-summary").content == "0 watched episodes"

        await app.push_screen(LibraryScreen(library_service=library))
        await pilot.pause()
        assert "1 favorites" in str(app.screen.query_one("#library-summary").content)

        await pilot.click("#refresh")
        await pilot.pause()
        assert "1 favorites" in str(app.screen.query_one("#library-summary").content)

    player.stop()
    database.dispose()
