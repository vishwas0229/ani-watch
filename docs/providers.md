# Providers and plugins

Providers are adapters behind a small protocol:

- check whether an anime/episode is available
- resolve a playable URI for authorized or user-owned media
- optionally honor a quality preference

The built-in local provider searches the configured local_media_root.

## Local file selection

Local media matches are deterministic and support common filename layouts. The provider prefers an exact title such as "Title - 01.ext", then unpadded episode numbers, "Episode 01", "E01", normalized title slugs such as "title-01.ext", and compact forms such as "title01.ext". It also supports an anime-folder layout such as "Title/Episode 01.ext". Within the same match class, paths are sorted lexically. Duplicate paths are resolved only once. Files or directories that become inaccessible during discovery are skipped so one bad filesystem entry does not abort provider resolution.

ProviderRegistry controls deterministic order. ProviderResolver tries providers in order, records health, applies the circuit breaker and falls back after a failure.

To add a provider, implement src/ani_watch/providers/contracts.py, add provider-specific parsing/network logic in its own module, and register it in the application bootstrap layer. Keep provider details out of the TUI and domain.

The project intentionally does not implement DRM bypassing or unauthorized copyrighted-stream access.
