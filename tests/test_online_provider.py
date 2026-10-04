from pathlib import Path

import pytest

from ani_watch.config.settings import AppSettings
from ani_watch.domain.errors import ConfigurationError, ProviderError
from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.bootstrap import build_provider_registry
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.providers.online import DirectUrlProvider


async def test_direct_url_provider_renders_episode_and_quality_placeholders() -> None:
    provider = DirectUrlProvider(
        "https://media.example/{title}/{anime_id}/{episode_padded}/{quality}.m3u8"
    )

    candidate = await provider.resolve(
        AnimeRef(42, "My Anime: The Test"),
        EpisodeRef(42, 3),
        quality="720p",
    )

    assert candidate == MediaCandidate(
        uri="https://media.example/My%20Anime%3A%20The%20Test/42/03/720p.m3u8",
        provider="online",
        quality="720p",
    )


async def test_direct_url_provider_accepts_fixed_direct_media_url() -> None:
    provider = DirectUrlProvider("https://media.example/episode-1.m3u8")

    assert await provider.available(AnimeRef(1, "Sample"), EpisodeRef(1, 7))


def test_direct_url_provider_rejects_unknown_placeholders() -> None:
    with pytest.raises(ValueError, match="Unsupported online URL placeholder"):
        DirectUrlProvider("https://media.example/{server}/{episode}.m3u8")


async def test_direct_url_provider_rejects_non_media_uri_scheme() -> None:
    provider = DirectUrlProvider("ftp://media.example/{episode}.m3u8")

    assert not await provider.available(AnimeRef(1, "Sample"), EpisodeRef(1, 1))
    with pytest.raises(ProviderError, match="http, https, or file"):
        await provider.resolve(AnimeRef(1, "Sample"), EpisodeRef(1, 1))


def test_bootstrap_registers_online_provider_and_respects_local_first(tmp_path: Path) -> None:
    settings = AppSettings(
        local_media_root=tmp_path,
        online_media_url_template="https://media.example/{anime_id}/{episode}.m3u8",
    )

    local_first = build_provider_registry(settings)
    assert local_first.names == ("local", "online")

    settings.playback.local_first = False
    online_first = build_provider_registry(settings)
    assert online_first.names == ("online", "local")


def test_bootstrap_wraps_invalid_online_template_as_configuration_error() -> None:
    settings = AppSettings(online_media_url_template="https://media.example/{unsupported}.m3u8")

    with pytest.raises(ConfigurationError, match="Unsupported online URL placeholder"):
        build_provider_registry(settings)
