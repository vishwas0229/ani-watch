# Ani-Watch Troubleshooting

## `ModuleNotFoundError`

Activate the repository environment:

```bash
conda activate ani-watch
python -m pip install -e ".[dev]"
```

## Conda runtime error

Ani-Watch requires an active Conda environment. Verify:

```bash
echo "$CONDA_PREFIX"
```

## PostgreSQL connection failure

Check the configured database URL, make sure PostgreSQL is running, create the target database/user, and run:

```bash
ani-watch migrate
```

## VLC startup failure

Verify that the host VLC/libVLC installation is present. The `python-vlc` package alone does not install the native VLC runtime.

## AniList authentication failure

Re-check the client ID, client secret, redirect URI, and OAuth application settings. Run `ani-watch login` again after clearing a stale token with `ani-watch logout`.

## AniList rate limit

The client honors the server's retry guidance for HTTP 429 responses and limits retries. Cached metadata can reduce repeated calls.

## Offline mode

With Redis enabled, cached metadata remains available for configured TTL periods. Provider and network failures are isolated so the TUI can continue to show local library data when external services are unavailable.
