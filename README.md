# Ani-Watch

A modular terminal-based anime discovery, tracking, and playback client.

## Development status

Ani-Watch is being built incrementally. The complete roadmap is tracked in GitHub Project #10, with each implementation step handled as an individual issue.

Current phase: **Foundation**

## Planned stack

- Python 3.12+
- uv
- Textual
- Typer
- AniList GraphQL API
- PostgreSQL + SQLAlchemy 2
- VLC/libVLC
- Redis (caching)
- Pydantic + httpx
- pytest + Ruff

## Foundation setup

Create the environment and install the development dependencies:

```bash
uv sync --extra dev
```

Run the CLI:

```bash
uv run ani-watch
```

Run the installation check:

```bash
uv run ani-watch doctor
```

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
uv run ruff format --check .
```

## Architecture

The project is intentionally split into layers so the terminal UI, CLI, business services, external APIs, storage, and player integration can evolve independently.

```text
CLI / TUI
   ↓
Application Services
   ↓
Domain
   ↓
Adapters
 ├── AniList
 ├── PostgreSQL
 ├── VLC
 └── Redis
```

## Roadmap

See [Project Roadmap: Ani-Watch](https://github.com/vishwas0229/ani-watch/issues/1) for the complete feature plan.

## License

MIT
