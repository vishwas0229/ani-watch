# Ani-Watch Installation

Ani-Watch uses a repository-owned Conda environment.

## Linux, macOS, and Windows

From the repository root:

```bash
conda env create -f environment.yml
conda activate ani-watch
python main.py
```

For an existing environment, install the package with:

```bash
python -m pip install -e ".[dev]"
```

Run the health check:

```bash
ani-watch doctor
```

The project requires Python 3.12 or newer and an active Conda environment.

## Optional runtime services

PostgreSQL is required for persistent library data. Configure `database.url` in the Ani-Watch settings file or provide the database URL through the environment-specific deployment configuration.

VLC/libVLC is required for media playback. The Python binding is installed by the project environment, while the VLC application/library must be present on the host operating system.

Redis is optional. Enable it in settings when a Redis server is available.

## AniList account

Public AniList metadata works without an account. Login is required only for user-specific list mutations and sync. Configure an AniList OAuth application and then use:

```bash
ani-watch login
```

