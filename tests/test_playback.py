import asyncio
from collections.abc import Callable

from ani_watch.config.settings import PlaybackSettings
from ani_watch.domain.episode import EpisodeItem
from ani_watch.domain.history import WatchHistoryEntry
from ani_watch.domain.models import AnimeRef
from ani_watch.player.manager import PlaybackManager
from ani_watch.providers.base import EpisodeProvider
from ani_watch.providers.registry import ProviderRegistry


class FakePlayer:
    def __init__(self) -> None:
        self.events: list[Callable[[], None]] = []
        self.loaded: str | None = None
        self.played = False
        self.position_value = 0

    def on_complete(self, callback):
        self.events.append(callback)

    def load(self, uri: str, **kwargs) -> None:
        self.loaded = uri

    def play(self) -> None:
        self.played = True

    def pause(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def seek(self, seconds: int) -> None:
        self.position_value = seconds

    def set_volume(self, volume: int) -> None:
        pass

    def position(self) -> int:
        return self.position_value


class FakeProvider(EpisodeProvider):
    name = "fake"

    async def episodes(self, anime):
        return [EpisodeItem(number=1, anime_id=anime.anilist_id, source_uri="file:///sample.mkv")]

    async def resolve(self, anime, episode_number):
        return EpisodeItem(number=episode_number, anime_id=anime.anilist_id, source_uri="file:///sample.mkv")


def test_playback_manager_resumes_saved_position() -> None:
    async def run() -> None:
        player = FakePlayer()
        manager = PlaybackManager(
            player,
            ProviderRegistry([FakeProvider()]),
            PlaybackSettings(),
        )
        await manager.play(
            AnimeRef(1, "Example"),
            1,
            history=[
                WatchHistoryEntry(
                    anime_id=1,
                    anime_title="Example",
                    episode_number=1,
                    progress_seconds=42,
                    duration_seconds=100,
                )
            ],
        )
        assert player.loaded == "file:///sample.mkv"
        assert player.position_value == 42
        assert player.played

    asyncio.run(run())
