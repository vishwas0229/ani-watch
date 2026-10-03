# Provider Architecture

Providers resolve episode sources without coupling the TUI or playback manager to a particular source implementation.

## Built-in provider

`local` scans configured directories for user-owned media files. It accepts common video extensions and recognizes episode numbering such as `S01E02` or `Episode 02`.

## Provider contract

Implement `EpisodeProvider` with:

- `episodes(anime)`
- `resolve(anime, episode_number)`

Register an implementation with `ProviderRegistry`.

The registry provides ordered discovery, health snapshots, and provider fallback. Circuit breakers isolate repeatedly failing providers.

Ani-Watch does not embed unauthorized stream extraction or DRM bypass logic. A provider should resolve only sources the user is authorized to access.
