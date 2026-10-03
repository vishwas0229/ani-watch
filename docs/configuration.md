# Ani-Watch Configuration

Settings are stored under the operating system's user configuration directory in a TOML file.

The most important sections are:

```toml
[database]
url = "postgresql+psycopg://ani_watch:ani_watch@localhost:5432/ani_watch"

[anilist]
graphql_url = "https://graphql.anilist.co"
client_id = "..."
client_secret = "..."
redirect_uri = "http://localhost:..."

[cache]
enabled = false
url = "redis://localhost:6379/0"
ttl_seconds = 900

[providers]
enabled = ["local"]
local_media_dirs = ["/path/to/anime"]
timeout_seconds = 15
failure_threshold = 3
recovery_seconds = 60

[playback]
quality = "1080p"
audio = "default"
subtitle = "default"
auto_next = true
skip_intro = false
skip_outro = false
local_first = true
volume = 80

[ui]
theme = "midnight"
episode_layout = "list"
density = "normal"
```

Do not commit tokens or client secrets. AniList access tokens are stored in the user's private configuration directory with restrictive permissions on POSIX systems.

Environment creation is intentionally kept in `environment.yml` so the project does not depend on a machine-specific Conda environment name.
