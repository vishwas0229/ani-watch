import pytest

from ani_watch.config.settings import PlaybackSettings
from ani_watch.domain.errors import PlaybackError
from ani_watch.player.vlc import VlcPlayer
from ani_watch.services.playback import PlaybackHooks, PlaybackManager


class FakePlayer:
    def __init__(self) -> None:
        self.play_calls = 0
        self.loaded = []
        self.volume = None
        self.position = 0

    def load(self, uri: str) -> None:
        self.loaded.append(uri)

    def play(self) -> None:
        self.play_calls += 1

    def pause(self) -> None:
        pass

    def set_time(self, value: int) -> None:
        self.position = value

    def get_time(self) -> int:
        return self.position

    def set_volume(self, value: int) -> None:
        self.volume = value

    def is_playing(self) -> bool:
        return self.play_calls > 0

    def stop(self) -> None:
        pass


def test_playback_manager_resumes_and_applies_volume() -> None:
    player = FakePlayer()
    manager = PlaybackManager(player, PlaybackSettings(volume=70))

    manager.start("file:///episode.mp4", resume_seconds=12)

    assert player.loaded == ["file:///episode.mp4"]
    assert player.position == 12_000
    assert player.volume == 70
    assert player.play_calls == 1


def test_skip_hooks_seek_to_detected_positions() -> None:
    player = FakePlayer()
    settings = PlaybackSettings(skip_intro=True, skip_outro=True)
    manager = PlaybackManager(player, settings)
    hooks = PlaybackHooks(
        intro_end=lambda _: 82,
        outro_start=lambda _: 1280,
    )

    manager.skip_intro(10, hooks)
    assert player.position == 82_000
    manager.skip_outro(900, hooks)
    assert player.position == 1_280_000
