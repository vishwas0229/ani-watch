from types import SimpleNamespace

from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.telegram import TelegramMediaProvider


def message(*, filename: str, text: str = "", message_id: int = 1, size: int = 1234):
    return SimpleNamespace(
        id=message_id,
        text=text,
        raw_text=text,
        file=SimpleNamespace(
            name=filename,
            size=size,
            mime_type="video/mp4",
            duration=120,
        ),
    )


def test_telegram_provider_matches_explicit_anilist_mapping() -> None:
    anime = AnimeRef(123, "Example Anime")
    episode = EpisodeRef(123, 4)
    item = message(
        filename="totally-different-name.mp4",
        text="My personal video\nanilist_id=123 episode=4",
    )

    assert TelegramMediaProvider._matches(item, anime, episode)


def test_telegram_provider_matches_title_and_episode_fallback() -> None:
    anime = AnimeRef(123, "Example Anime")
    episode = EpisodeRef(123, 2)
    item = message(filename="Example Anime - Episode 02.mp4")

    assert TelegramMediaProvider._matches(item, anime, episode)


def test_telegram_provider_rejects_wrong_episode() -> None:
    anime = AnimeRef(123, "Example Anime")
    episode = EpisodeRef(123, 2)
    item = message(filename="Example Anime - Episode 03.mp4")

    assert not TelegramMediaProvider._matches(item, anime, episode)


def test_telegram_provider_normalizes_titles() -> None:
    assert TelegramMediaProvider._normalized("My: Example! 2") == "my example 2"


def test_telegram_provider_extracts_episode_labels() -> None:
    assert TelegramMediaProvider._episode_number("Episode 07.mp4") == 7
    assert TelegramMediaProvider._episode_number("ep-3-final.mp4") == 3


def test_telegram_provider_rejects_non_video_media() -> None:
    from types import SimpleNamespace

    photo = SimpleNamespace(
        id=1,
        text="Example Anime Episode 1",
        raw_text="Example Anime Episode 1",
        video=None,
        file=SimpleNamespace(
            name="cover.jpg",
            size=123,
            mime_type="image/jpeg",
            duration=None,
        ),
    )

    assert not TelegramMediaProvider._is_streamable_media(photo)
