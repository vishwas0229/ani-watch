from types import SimpleNamespace

import pytest

import ani_watch.providers.streamlink as streamlink_provider
from ani_watch.domain.errors import ProviderError
from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.providers.streamlink import StreamlinkProvider


async def test_streamlink_provider_resolves_requested_quality(monkeypatch) -> None:
    fake_stream = SimpleNamespace(url="https://cdn.example/720p.m3u8")

    def fake_streams(url: str):
        assert url == "https://service.example/watch/42/03"
        return {
            "480p": SimpleNamespace(url="https://cdn.example/480p.m3u8"),
            "720p": fake_stream,
            "1080p": SimpleNamespace(url="https://cdn.example/1080p.m3u8"),
            "best": SimpleNamespace(url="https://cdn.example/1080p.m3u8"),
        }

    monkeypatch.setattr(streamlink_provider.streamlink, "streams", fake_streams)
    provider = StreamlinkProvider(
        "https://service.example/watch/{anime_id}/{episode_padded}"
    )

    candidate = await provider.resolve(
        AnimeRef(42, "Sample Anime"),
        EpisodeRef(42, 3),
        quality="720p",
    )

    assert candidate == MediaCandidate(
        uri="https://cdn.example/720p.m3u8",
        provider="streamlink",
        quality="720p",
    )


async def test_streamlink_provider_prefers_best_for_auto(monkeypatch) -> None:
    monkeypatch.setattr(
        streamlink_provider.streamlink,
        "streams",
        lambda url: {
            "720p": SimpleNamespace(url="https://cdn.example/720p.m3u8"),
            "best": SimpleNamespace(url="https://cdn.example/1080p.m3u8"),
        },
    )
    candidate = await provider.resolve(
        AnimeRef(42, "Sample"),
        EpisodeRef(42, 1),
        quality="auto",
    )

    assert candidate.uri == "https://cdn.example/1080p.m3u8"
    assert candidate.quality == "best"


async def test_streamlink_provider_rejects_unplayable_stream(monkeypatch) -> None:
    monkeypatch.setattr(
        streamlink_provider.streamlink,
        "streams",
        lambda url: {"best": object()},
    )
    provider = StreamlinkProvider("https://service.example/watch/{episode}")

    with pytest.raises(ProviderError, match="cannot be passed directly to VLC"):
        await provider.resolve(
            AnimeRef(42, "Sample"),
            EpisodeRef(42, 1),
        )


async def test_streamlink_provider_wraps_resolution_errors(monkeypatch) -> None:
    def fail(url: str):
        raise RuntimeError("plugin failed")

    monkeypatch.setattr(streamlink_provider.streamlink, "streams", fail)
    provider = StreamlinkProvider("https://service.example/watch/{episode}")

    with pytest.raises(ProviderError, match="could not resolve the online source"):
        await provider.resolve(
            AnimeRef(42, "Sample"),
            EpisodeRef(42, 1),
        )


def test_streamlink_provider_rejects_unknown_placeholders() -> None:
    with pytest.raises(ValueError, match="Unsupported Streamlink URL placeholder"):
        StreamlinkProvider("https://service.example/{server}/{episode}")


async def test_streamlink_provider_resolve_url_uses_instance(monkeypatch) -> None:
    monkeypatch.setattr(
        streamlink_provider.streamlink,
        "streams",
        lambda url: {"best": type("Stream", (), {"url": "https://cdn.example/episode.m3u8"})()},
    )
    provider = StreamlinkProvider("https://service.example/watch/{episode}")

    candidate = await StreamlinkProvider.resolve_url(
        "https://service.example/watch/1",
        quality="auto",
    )

    assert candidate.uri == "https://cdn.example/episode.m3u8"
    assert candidate.provider == "streamlink"


async def test_streamlink_provider_resolve_url_supports_class_call(monkeypatch) -> None:
    monkeypatch.setattr(
        streamlink_provider.streamlink,
        "streams",
        lambda url: {
            "best": SimpleNamespace(url="https://cdn.example/class-call.m3u8"),
        },
    )

    candidate = await StreamlinkProvider.resolve_url(
        "https://service.example/watch/1",
        quality="auto",
    )

    assert candidate == MediaCandidate(
        uri="https://cdn.example/class-call.m3u8",
        provider="streamlink",
        quality="best",
    )
