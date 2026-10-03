# Ani-Watch

A modular terminal-based anime discovery, tracking, and playback client.

## Development status

Ani-Watch is being built incrementally. The complete roadmap is tracked in GitHub Project #10, with each implementation step handled as an individual issue.

Current phase: **TUI**

## Supported environment

Ani-Watch is **Conda-only**. The application requires an active Conda environment at runtime and will stop with a clear error if started outside Conda.

Supported Python version: **3.12+**

## Planned stack

- Conda
- Python 3.12+
- Textual
- Typer
- AniList GraphQL API
- PostgreSQL + SQLAlchemy 2
- VLC/libVLC
- Redis (caching)
- Pydantic + httpx
- pytest + Ruff

## Conda setup

### Recommended: create the project environment

From the repository root:

```bash
conda env create -f environment.yml
conda activate ani-watch
```

The environment file installs the project in editable mode together with the development dependencies.

### Existing Conda environment

You can also use an existing Conda environment such as `dev`:

```bash
conda activate dev
python -m pip install -e ".[dev]"
```

### Verify Conda

```bash
conda info --envs
echo "$CONDA_PREFIX"
```

`CONDA_PREFIX` should point to the active Conda environment.

## Run Ani-Watch

From the repository root:

```bash
python main.py
```

The packaged entry points are also available after the editable install:

```bash
ani-watch
ani-watch doctor
python -m ani_watch
```

All application entry points require an active Conda environment.

## Run tests

```bash
python -m pytest
```

## Run linting

```bash
python -m ruff check .
python -m ruff format --check .
```

## Architecture

Ani-Watch uses explicit package boundaries so the UI, business logic, external services, persistence, and playback engine can evolve independently.

```text
CLI / TUI
    ↓
Application Services
    ↓
Domain
    ↓
Adapters / Infrastructure
    ├── Metadata (AniList)
    ├── Storage (PostgreSQL)
    ├── Player (VLC)
    ├── Providers / Resolvers
    └── Cache (Redis)
```

See [Architecture](docs/architecture.md) for the package responsibilities and dependency direction.

## Roadmap

See [Project Roadmap: Ani-Watch](https://github.com/vishwas0229/ani-watch/issues/1) for the complete feature plan.

## License

MIT
