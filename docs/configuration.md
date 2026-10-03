# Configuration

Ani-Watch stores user-facing settings in its platform configuration directory.

The runtime requires an active Conda environment. The repository's default environment name is `ani-watch`.

## Key settings

- `database_url`: SQLAlchemy URL. SQLite is used by default for local development; PostgreSQL URLs are supported.
- `redis_url`: optional Redis URL. When configured, the TUI metadata cache uses Redis with an in-process memory fallback.
- `local_media_root`: optional path for user-owned local media.
- `playback.quality`: `1080p`, `720p`, `480p`, or `auto`.
- `playback.audio`: `default`. Track-specific selection is handled by the VLC playback controls.
- `playback.subtitle`: `default`. Track-specific selection is handled by the VLC playback controls.
- `playback.auto_next`: enable automatic next-episode orchestration.
- `playback.local_first`: prefer configured local media.
- `ui.theme`: `midnight`, `mono`, or `high-contrast`.
- `ui.density`: `compact`, `normal`, or `comfortable`.
- `network.timeout_seconds`: HTTP timeout.
- `network.retries`: retry count.
- `network.offline_mode`: use cached metadata only.

Unsupported values are rejected during configuration validation. When a persisted TOML file is invalid, Ani-Watch reports a configuration error rather than exposing the underlying validation payload; edit or remove the configuration file and restart to recover with typed defaults. New UI or playback modes must be added to the typed settings model and the corresponding TUI controls before they can be persisted.

### SQLite initialization

For a file-backed SQLite URL, Ani-Watch creates the database's parent directory automatically before opening the engine. This allows a fresh installation to use the default platform data path without requiring a manual directory-creation step.

In-memory SQLite URLs such as `sqlite:///:memory:` are left unchanged.

AniList OAuth client credentials should be supplied through environment/configuration management appropriate for your deployment. Access tokens are stored through the OS credential store rather than written to normal log files.
