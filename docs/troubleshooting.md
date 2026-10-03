# Troubleshooting

## Missing Python modules

Activate the repository environment and install the project:

```bash
conda activate ani-watch
python -m pip install -e ".[dev]"
```

## Conda runtime guard

Ani-Watch requires an active Conda environment. Verify it with:

```bash
echo "$CONDA_PREFIX"
```

PowerShell:

```powershell
$env:CONDA_PREFIX
```

## VLC errors

Install VLC/libVLC for the operating system. python-vlc is the Python binding; the native VLC runtime is still required.

## PostgreSQL errors

Check the configured SQLAlchemy URL, database availability, credentials and the PostgreSQL driver.

## AniList failures

Public metadata requests do not need an account token. Account list reads and mutations require AniList OAuth authentication. Network errors are retried according to the configured retry policy.

## Redis failures

Redis is optional. The in-memory cache remains available for local and degraded operation.

## TUI layout

Ani-Watch uses responsive Textual layouts. On narrow terminals the home dashboard and settings reorganize into vertical sections; enlarge the terminal for a wider multi-column view.
