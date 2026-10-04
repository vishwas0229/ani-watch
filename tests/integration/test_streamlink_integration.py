"""Opt-in online integration checks for Streamlink."""

from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest
import streamlink

PUBLIC_HLS_SAMPLE = (
    "https://devstreaming-cdn.apple.com/videos/streaming/examples/"
    "bipbop_4x3/bipbop_4x3_variant.m3u8"
)


@pytest.mark.integration
def test_streamlink_resolves_public_hls_sample() -> None:
    """Resolve a public HLS sample through the real Streamlink library."""
    if os.getenv("ANI_WATCH_RUN_ONLINE_TESTS") != "1":
        pytest.skip("Set ANI_WATCH_RUN_ONLINE_TESTS=1 to run network integration tests.")

    streams = streamlink.streams(PUBLIC_HLS_SAMPLE)
    assert streams, "Streamlink returned no streams for the public HLS sample."

    best = streams.get("best")
    if best is None:
        best = next(iter(streams.values()))

    url = getattr(best, "url", None)
    assert isinstance(url, str) and url, "Resolved stream did not expose a playable URL."

    parsed = urlparse(url)
    assert parsed.scheme in {"http", "https"}
    assert parsed.netloc
