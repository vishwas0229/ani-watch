# Configuration

Ani-Watch stores user-facing settings in its platform configuration directory.

The runtime requires an active Conda environment. The repository's default environment name is `ani-watch`.

## Key settings

- `database_url`: SQLAlchemy URL. SQLite is used by default for local development; PostgreSQL URLs are supported.
- `redis_url`: optional Redis URL.
- `local_media_root`: optional path for user-owned local media.
- `playback.quality`: preferred quality label.
- `playback.audio`: preferred audio mode.
- `playback.subtitle`: preferred subtitle mode.
- `playback.auto_next`: enable automatic next-episode orchestration.
- `playback.local_first`: prefer configured local media.
- `ui.theme`: `midnight`, `mono`, or `high-contrast`.
- `ui.density`: compact, normal, or comfortable.
- `network.timeout_seconds`: HTTP timeout.
- `network.retries`: retry count.

### SQLite initialization

For a file-backed SQLite URL, Ani-Watch creates the database's parent directory automatically before opening the engine. This allows a fresh installation to use the default platform data path without requiring a manual directory-creation step.

In-memory SQLite URLs such as `sqlite:///:memory:` are left unchanged.

AniList OAuth client credentials should be supplied through environment/configuration management appropriate for your deployment. Access tokens are stored through the OS credential store rather than written to normal log files.
