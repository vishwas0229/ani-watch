#!/usr/bin/env python3
"""Manual Streamlink -> VLC smoke test using a public HLS sample."""

from __future__ import annotations

import argparse
import asyncio
import time
from urllib.parse import urlparse

from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.player.vlc import VlcPlayer
from ani_watch.providers.streamlink import StreamlinkProvider

PUBLIC_HLS_SAMPLE = (
    "https://devstreaming-cdn.apple.com/videos/streaming/examples/"
    "bipbop_4x3/bipbop_4x3_variant.m3u8"
)


async def resolve_sample() -> str:
    provider = StreamlinkProvider(PUBLIC_HLS_SAMPLE)
    candidate = await provider.resolve(
        AnimeRef(1, "Streamlink Integration Sample"),
        EpisodeRef(1, 1),
        quality="auto",
    )
    return candidate.uri


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seconds",
        type=float,
        default=5.0,
        help="Seconds to keep VLC playing before stopping (default: 5).",
    )
    args = parser.parse_args()

    uri = asyncio.run(resolve_sample())
    parsed = urlparse(uri)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"Streamlink returned an invalid playable URL: {uri}")

    print(f"Resolved stream: {uri}")
    player = VlcPlayer()
    try:
        player.load(uri)
        player.play()
        print(f"VLC playback started; running for {args.seconds:g}s...")
        time.sleep(max(0.5, args.seconds))
        print(f"VLC state: {player.state()}")
        print(f"VLC position: {player.get_time()} ms")
    finally:
        player.stop()
        player.release()

    print("Streamlink -> VLC smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
