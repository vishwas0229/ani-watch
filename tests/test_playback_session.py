from dataclasses import dataclass

import pytest

from ani_watch.config.settings import PlaybackSettings
from ani_watch.domain.models import AnimeRef, EpisodeItem, EpisodeRef
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.services.playback import PlaybackManager, PlaybackSession


@dataclass
class FakeProgress:
    position_seconds: int
    duration_seconds: int | None
    completed: bool = False


class FakeProgressRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[int, int], FakeProgress] = {}
        self.saves = 0

    def get(self, anime_id: int, episode_number: int) -> FakeProgress | None:
        return self.records.get((anime_id, episode_number))

    def save(
        self,
        anime_id: int,
        episode_number: int,
        position_seconds: int,
        duration_seconds: int | None,
        completed: bool = False,
    ) -> None:
        self.saves += 1
        self.records[(anime_id, episode_number)] = FakeProgress(
            position_seconds=position_seconds,
            duration_seconds=duration_seconds,
            completed=completed,
        )


class FakeLibrary:
    def __init__(self) -> None:
        self.progress = FakeProgressRepository()
        self.save_calls: list[tuple[int, int, int, int | None]] = []
        self.history_count = 0

    def save_progress(
        self,
        anime_id: int,
        episode_number: int,
        position_seconds: int,
        duration_seconds: int | None,
    ) -> None:
        self.save_calls.append((anime_id, episode_number, position_seconds, duration_seconds))
        completed = (
            duration_seconds is not None
            and duration_seconds > 0
            and position_seconds >= duration_seconds * 0.9
        )
        self.progress.save(
            anime_id,
            episode_number,
            position_seconds,
            duration_seconds,
            completed=completed,
        )
        if completed:
            self.history_count += 1


class FakePlayer:
    def __init__(self, *, duration_ms: int = 120_000) -> None:
        self.duration_ms = duration_ms
        self.position_ms = 0
        self.playing = False
        self.loaded: list[str] = []

    def load(self, uri: str) -> None:
        self.loaded.append(uri)
        self.position_ms = 0

    def play(self) -> None:
        self.playing = True

    def pause(self) -> None:
        self.playing = False

    def stop(self) -> None:
        self.playing = False

    def set_time(self, milliseconds: int) -> None:
        self.position_ms = milliseconds

    def get_time(self) -> int:
        return self.position_ms

    def get_length(self) -> int:
        return self.duration_ms

    def set_volume(self, volume: int) -> None:
        pass

    def is_playing(self) -> bool:
        return self.playing

    def is_complete(self) -> bool:
        return self.duration_ms > 0 and self.position_ms >= self.duration_ms and not self.playing


class FakeResolver:
    async def resolve(
        self,
        anime: AnimeRef,
        episode: EpisodeRef,
        *,
        quality: str | None = None,
    ) -> MediaCandidate:
        return MediaCandidate(
            uri=f"file:///anime-{anime.anilist_id}-episode-{episode.number}.mp4",
            provider="fake",
            quality=quality,
        )


def make_session(
    clock,
    *,
    interval_seconds: float = 5.0,
) -> tuple[PlaybackSession, FakePlayer, FakeLibrary]:
    player = FakePlayer()
    manager = PlaybackManager(player, PlaybackSettings())
    library = FakeLibrary()
    session = PlaybackSession(
        manager,
        FakeResolver(),
        library,
        clock=clock,
        progress_interval_seconds=interval_seconds,
    )
    return session, player, library


@pytest.mark.asyncio
async def test_tick_persists_immediately_then_only_after_interval() -> None:
    current_time = [0.0]
    session, player, library = make_session(lambda: current_time[0])
    anime = AnimeRef(100, "Sample Anime")
    episode = EpisodeItem(number=1, title="Episode 1")

    await session.start(anime, episode)
    player.position_ms = 10_000

    assert session.tick() is False
    assert library.save_calls == [(100, 1, 10, 120)]

    player.position_ms = 20_000
    current_time[0] = 3
    assert session.tick() is False
    assert len(library.save_calls) == 1

    current_time[0] = 5
    assert session.tick() is False
    assert library.save_calls[-1] == (100, 1, 20, 120)


@pytest.mark.asyncio
async def test_tick_persists_while_paused_even_before_interval() -> None:
    current_time = [0.0]
    session, player, library = make_session(lambda: current_time[0])

    await session.start(AnimeRef(100, "Sample Anime"), EpisodeItem(number=1))
    player.position_ms = 7_500
    player.pause()
    current_time[0] = 1

    assert session.tick() is False
    assert library.save_calls[-1] == (100, 1, 7, 120)


@pytest.mark.asyncio
async def test_completion_is_reported_once_and_history_is_not_duplicated() -> None:
    current_time = [0.0]
    session, player, library = make_session(lambda: current_time[0])
    await session.start(AnimeRef(100, "Sample Anime"), EpisodeItem(number=1))

    player.position_ms = 120_000
    player.playing = False

    assert session.tick() is True
    assert library.history_count == 1
    assert session.completion_pending() is False

    current_time[0] = 10
    assert session.tick() is False
    assert library.history_count == 1


@pytest.mark.asyncio
async def test_stop_persists_current_position_and_clears_session() -> None:
    current_time = [0.0]
    session, player, library = make_session(lambda: current_time[0])
    await session.start(AnimeRef(100, "Sample Anime"), EpisodeItem(number=1))

    player.position_ms = 4_500
    session.stop()

    assert library.save_calls == [(100, 1, 4, 120)]
    assert not session.active
    assert not player.playing
