# Providers and plugins

Providers are adapters behind a small protocol:

- check whether an anime/episode is available
- resolve a playable URI for authorized or user-owned media
- optionally honor a quality preference

The built-in local provider searches the configured local_media_root.

## Local file selection

Local media matches are deterministic and support common filename layouts. The provider prefers an exact title such as "Title - 01.ext", then unpadded episode numbers, "Episode 01", "E01", normalized title slugs such as "title-01.ext", and compact forms such as "title01.ext". It also supports an anime-folder layout such as "Title/Episode 01.ext". Within the same match class, paths are sorted lexically. Duplicate paths are resolved only once. Files or directories that become inaccessible during discovery are skipped so one bad filesystem entry does not abort provider resolution.

ProviderRegistry controls deterministic order. ProviderResolver tries providers in order, records health, applies the circuit breaker and falls back after a failure. A targeted provider name can be supplied when an action must use one provider explicitly.

To add a provider, implement src/ani_watch/providers/contracts.py, add provider-specific parsing/network logic in its own module, and register it in the application bootstrap layer. Keep provider details out of the TUI and domain.

The project intentionally does not implement DRM bypassing or unauthorized copyrighted-stream access.

## Online watching

Ani-Watch has two online-provider paths:

1. **Streamlink** accepts a configured streaming page or direct stream URL and resolves supported services/protocols into a playable stream. Streamlink provides a plugin system for supported services and supports direct HLS/DASH/HTTP stream protocols. VOD support varies by service, because Streamlink primarily targets streaming services and has limited VOD coverage.
2. **Direct media** is the deterministic fallback for a user-authorized HLS playlist, MP4, or similar media endpoint that VLC can open directly.

Configure either path in Settings. Streamlink is preferred when both are configured; direct media is used as the second online provider.

### Streamlink URL template

The Streamlink template may use:

- `{anime_id}`
- `{episode}`
- `{episode_padded}`
- `{quality}`
- `{title}` (URL-encoded)

Example:

```text
https://service.example/watch/{anime_id}/{episode_padded}
```

Ani-Watch runs Streamlink asynchronously so the TUI is not blocked while a supported service is resolved. For streams exposing an HTTP/HLS URL, that URL is handed to the existing ProviderResolver → PlaybackSession → VLC pipeline, preserving resume, progress tracking and auto-next.

### Direct media URL template

The direct-media template uses the same placeholders. For example:

```text
https://media.example/anime/{anime_id}/episode/{episode_padded}.m3u8
```


### Real Streamlink integration test

The repository includes an opt-in network integration test using a public HLS sample documented by Streamlink:

```bash
conda activate ani-watch
ANI_WATCH_RUN_ONLINE_TESTS=1 python -m pytest tests/integration/test_streamlink_integration.py -v
```

For a desktop VLC smoke test of the complete Streamlink → Ani-Watch provider → VLC path:

```bash
python scripts/streamlink_vlc_smoke.py --seconds 5
```

The integration test is opt-in so normal CI remains deterministic. Streamlink documents that `streamlink.streams()` returns Stream objects and that HLS streams expose a `url` attribute suitable for playback. See the Streamlink Python API documentation.

Use only media endpoints you are authorized to access. An external watch page is not automatically a direct media URL, and Ani-Watch does not implement DRM bypassing or unauthorized source scraping.

