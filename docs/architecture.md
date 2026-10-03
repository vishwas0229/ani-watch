# Ani-Watch Architecture

## Layers

Ani-Watch uses explicit package boundaries:

- **domain** — provider-independent models such as anime details, episodes, favorites, and watch history.
- **services** — orchestration contracts and library/playback workflows.
- **metadata** — AniList GraphQL client, metadata mapping, and cache-aware access.
- **storage** — SQLAlchemy ORM, PostgreSQL repositories, and Alembic migrations.
- **player** — VLC/libVLC adapter and playback intelligence.
- **providers** — source adapters, registry, resolver behavior, health checks, fallback, and circuit breakers.
- **auth** — AniList OAuth and local token lifecycle.
- **cache** — optional Redis adapter.
- **tui** — Textual presentation and keyboard navigation.
- **infra** — logging and reliability primitives.
- **cli** — terminal commands for TUI launch, database migration, search, authentication, and sync.

## Dependency direction

```text
TUI / CLI
    |
    v
Application Services
    |
    v
Domain
    ^
    |
Adapters / Infrastructure
  +-- Metadata (AniList)
  +-- Storage (PostgreSQL)
  +-- Player (VLC/libVLC)
  +-- Providers
  +-- Cache (Redis)
  +-- Auth
```

The domain never imports a provider, database, network client, or player library.

## Runtime data flow

### Metadata

```text
SearchScreen
   -> MetadataService
      -> AniListClient
         -> GraphQL endpoint
```

The client implements timeout, retry, and HTTP 429 handling. Cache-aware access can serve previously stored metadata when the external API is unavailable.

### Library

```text
TUI
  -> LibraryService
     -> Repository
        -> SQLAlchemy
           -> PostgreSQL
```

Favorites, episodes, watch history, playback progress, and settings are persisted locally.

### Playback

```text
Episode selection
   -> ProviderRegistry
      -> EpisodeProvider
         -> EpisodeItem(source_uri)
   -> PlaybackManager
      -> VlcPlayer
         -> libVLC
```

Provider failures are isolated by circuit breakers. Playback intelligence handles resume position, automatic next-episode callbacks, local-first resolution, recovery, and configurable intro/outro skip hooks.

## Configuration

Configuration is validated with Pydantic and persisted as TOML. Secrets used for AniList OAuth are stored separately from normal settings with restrictive POSIX permissions.

The repository ships one Conda environment definition so development is reproducible without depending on an individual developer's environment name.
