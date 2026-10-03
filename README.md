# Ani-Watch

A modular, Conda-based terminal anime discovery, tracking, library, and playback client.

## Current status

Ani-Watch is now an integrated TUI foundation with metadata, local library persistence, provider routing, playback orchestration, reliability, synchronization, and packaging foundations.

## Supported environment

Ani-Watch is **Conda-only**.

Create the repository environment:

```bash
conda env create -f environment.yml
conda activate ani-watch
```

Run the application from the repository root:

```bash
python main.py
```

The environment name `ani-watch` is owned by the project; no machine-specific Conda environment is required.

## Main TUI

```text
Home
 ├── Search
 │    └── Anime Details
 │         └── Episodes
 │              └── Player handoff
 ├── History
 ├── Favorites
 ├── Library
 └── Settings
```

Primary shortcuts include `/` Search, `r` History, `f` Favorites, `l` Library, `,` Settings, and `q` Quit.

## Stack

- Python 3.12+
- Conda
- Textual
- Typer
- AniList GraphQL
- Pydantic + httpx
- PostgreSQL + SQLAlchemy 2 + Alembic
- VLC/libVLC through python-vlc
- Redis caching
- pytest + Ruff

AniList exposes public metadata without authentication; user-specific list changes require OAuth. GraphQL requests use the official AniList endpoint, and the application stores only local library/tracking data rather than using AniList as a backup datastore.

## Database

Configure the PostgreSQL URL in the user settings file, then apply migrations:

```bash
ani-watch migrate
```

The default database URL is:

```text
postgresql+psycopg://ani_watch:ani_watch@localhost:5432/ani_watch
```

For tests, SQLite can be used without changing the production PostgreSQL configuration.

## Metadata and AniList

Search and details use the AniList GraphQL API. Authentication is needed for user list synchronization and mutations.

Configure AniList OAuth application credentials in user settings or environment-specific configuration, then:

```bash
ani-watch login
ani-watch sync
ani-watch logout
```

Public metadata search does not require a token.

## Playback and providers

Playback is intentionally separated from metadata and the TUI.

The built-in `local` provider resolves user-owned media from configured directories. Provider registry fallback and circuit breaking isolate failing adapters. VLC controls include load/play, pause/resume/stop, seek, volume, completion detection, audio/subtitle track selection, and playback preference hooks.

Ani-Watch does not embed DRM bypass or unauthorized stream extraction. Providers should resolve only sources the user is authorized to access.

## Caching and reliability

Redis is optional. When enabled, metadata can be cached by key with a configurable TTL. Network requests have bounded retries, timeout handling, and explicit 429 rate-limit handling. Provider errors are isolated through circuit breakers, allowing local features to remain usable during external outages.

## Development commands

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Run the installation health check:

```bash
ani-watch doctor
```

## Documentation

- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)
- [Providers](docs/providers.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Repository layout

```text
main.py
environment.yml
pyproject.toml
src/ani_watch/
├── auth/
├── cache/
├── cli/
├── config/
├── domain/
├── infra/
├── metadata/
├── player/
├── providers/
├── services/
├── storage/
└── tui/
migrations/
tests/
docs/
```

## Roadmap

See [Project Roadmap: Ani-Watch](https://github.com/vishwas0229/ani-watch/issues/1) for the tracked implementation plan.

## License

MIT
