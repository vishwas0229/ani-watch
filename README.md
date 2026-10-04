# Ani-Watch

A modular terminal-based anime discovery, tracking, library and playback client.

## Current status

The application contains the end-to-end architecture for the TUI, AniList metadata, local persistence, playback, providers, synchronization, caching and reliability layers. It also supports an optional Telegram-backed personal media source.

## Supported runtime

Ani-Watch is **Conda-only** and requires the repository environment:

```
conda env create -f environment.yml
conda activate ani-watch
python -m pip install -e ".[dev]"
```

The primary source-checkout launcher is:

```
python main.py
```

## Features

- Textual TUI with Home, Search, Details, Episodes, History, Favorites, Library and Settings screens
- Keyboard navigation with global shortcuts and responsive terminal layouts
- Theme selection and persisted UI/playback preferences
- AniList GraphQL search and anime details
- SQLAlchemy 2 persistence with SQLite for local use and PostgreSQL support
- Initial Alembic migration
- Watch history, favorites, progress, continue-watching and library statistics
- VLC/libVLC playback adapter with pause, seek, volume and audio/subtitle track selection
- Resume playback, auto-next configuration, skip hooks, local-first preference and recovery
- Provider registry, resolver fallback, health monitoring and circuit breaking
- Built-in local-file provider for user-owned media
- Streamlink-backed online playback for supported services/protocols, with direct-media fallback
- Optional Telegram MTProto provider for authorized personal media in a private channel
- Range-capable local Telegram gateway that streams media to VLC without first downloading the complete file
- AniList OAuth login helpers, secure OS credential storage, list sync and mutations
- Memory cache, optional Redis cache, timeout/retry handling, rate-limit handling and offline/degraded mode
- Conda installers for Linux, macOS and Windows
- GitHub Actions CI and tagged release automation

## External requirements

The Python dependencies are installed through the Conda environment. VLC/libVLC is required by the playback adapter. PostgreSQL and Redis are optional services enabled through configuration. Telegram is optional and requires a Telegram application created through my.telegram.org.

## Configuration

User configuration is stored in the platform configuration directory. See [Configuration](docs/configuration.md).

Important runtime settings include:

- database URL
- optional Redis URL
- local media root
- Streamlink URL template and optional direct online media URL template
- optional Telegram API ID, private channel and scan limit
- playback quality, audio, subtitle, volume, auto-next and local-first preferences
- UI theme and density
- HTTP timeout and retry count
- AniList OAuth application settings

The Telegram API hash is stored in the operating-system keyring rather than the configuration file. The Telegram MTProto session is stored in the platform data directory and is ignored by Git.

## Telegram personal media

Ani-Watch keeps the anime catalog and episode metadata in AniList. Telegram is only a playback source for authorized/user-owned media.

Create the Telegram application at:

https://my.telegram.org/apps

Then configure Ani-Watch:

```
ani-watch telegram configure
ani-watch telegram login
ani-watch telegram status
ani-watch telegram sync
```

Recommended Telegram caption mapping for exact episode matching:

```
anilist_id=123 episode=1
```

You can also use the fallback filename format:

```
Naruto - Episode 01.mp4
```

The Telegram provider is inserted into the normal provider resolver, so the existing AniList-backed episode UI remains unchanged. When Telegram resolves an authorized media message, VLC receives a local HTTP URL and the gateway retrieves requested byte ranges from Telegram on demand.

See [Telegram personal media](docs/telegram.md) for the complete setup and troubleshooting guide.

## AniList account commands

After configuring your AniList OAuth client ID, client secret, and redirect URI:

```
ani-watch auth login
ani-watch auth status
ani-watch auth sync
ani-watch auth sync --no-pull --push
ani-watch auth logout
```

The login flow prints the AniList authorization URL and accepts either the returned authorization code or the full callback URL. Tokens are stored through the operating system credential store and are never written to application logs.

## Documentation

- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Telegram personal media](docs/telegram.md)
- [Architecture](docs/architecture.md)
- [Providers](docs/providers.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Development checks

```
conda activate ani-watch
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## Project roadmap

The implementation plan is tracked in GitHub Project #10 and [Project Roadmap: Ani-Watch](https://github.com/vishwas0229/ani-watch/issues/1).

## Safety boundary

The provider layer is intended for authorized or user-owned media sources. Ani-Watch does not implement DRM bypassing or unauthorized access to copyrighted streams.

## License

MIT
