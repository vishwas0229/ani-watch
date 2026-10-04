"""Opt-in online integration checks for Streamlink."""

from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest

from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.streamlink import StreamlinkProvider

PUBLIC_HLS_SAMPLE = (
    "https://devstreaming-cdn.apple.com/videos/streaming/examples/"
    "bipbop_4x3/bipbop_4x3_variant.m3u8"
)


@pytest.mark.integration
async def test_streamlink_provider_resolves_public_hls_sample() -> None:
    """Resolve a public HLS sample through the real Streamlink provider."""
    if os.getenv("ANI_WATCH_RUN_ONLINE_TESTS") != "1":
        pytest.skip("Set ANI_WATCH_RUN_ONLINE_TESTS=1 to run network integration tests.")

    provider = StreamlinkProvider(PUBLIC_HLS_SAMPLE)
    candidate = await provider.resolve(
        AnimeRef(1, "Streamlink Integration Sample"),
        EpisodeRef(1, 1),
        quality="auto",
    )

    parsed = urlparse(candidate.uri)
    assert parsed.scheme in {"http", "https"}
    assert parsed.netloc
    assert candidate.provider == "streamlink"
