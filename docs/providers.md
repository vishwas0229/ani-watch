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

The TUI can use the AniList `streamingEpisodes` field to find links to legal external streaming episode pages. These links are opened in the user's default browser rather than treated as direct media files.

For VLC-based online playback, configure an authorized **direct media URL template** in Settings → Online media URL. The template may use:

- `{anime_id}`
- `{episode}`
- `{episode_padded}`
- `{quality}`
- `{title}` (URL-encoded)

For example:

```text
https://media.example/anime/{anime_id}/episode/{episode_padded}.m3u8
```

The online provider passes the rendered URL into the existing ProviderResolver → PlaybackSession → VLC pipeline. HLS playlists such as `.m3u8` and direct video files can therefore use the same resume, progress tracking and auto-next features as local media, provided the configured endpoint is directly playable by VLC.

Use only media endpoints you are authorized to access. An external watch page is not automatically a direct media URL and should remain in the browser flow.
