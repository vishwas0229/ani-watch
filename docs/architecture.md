# Architecture

Ani-Watch is a terminal-first application with dependency inversion between presentation, domain, external services, persistence and playback.

```text
TUI / CLI
    |
Application Services
    |
Domain Models
    |
+---+---------+------------+----------------+
|             |            |                |
Metadata    Storage      Providers        Player
AniList     SQLAlchemy   Registry         VLC/libVLC
            PostgreSQL   Resolver
                         Health/Circuit
    |
Cache / Reliability
    |
Memory / Redis
```

## Boundaries

### TUI
Textual screens render domain data and dispatch actions. Provider-specific networking and SQL do not live in screens.

### Metadata
The AniList adapter uses GraphQL requests and maps response data into stable, provider-neutral models. Network retry, timeout and rate-limit behavior is centralized in the client.

### Storage
SQLAlchemy 2 models and repositories provide the persistence boundary. SQLite is suitable for local use and PostgreSQL is supported through the same interface. Alembic is the canonical schema migration mechanism; the CLI and database bootstrap execute the configured migration revisions instead of maintaining a separate schema-version table.

### Playback
The VLC adapter owns libVLC calls. Playback services provide resume, pause, seek, volume, audio/subtitle selection, auto-next configuration, local-first preference, skip hooks, recovery, periodic progress persistence and completion lifecycle tracking.

### Providers
The provider registry owns discovery and configuration order. The resolver provides fallback. Health metrics and circuit breaking isolate unhealthy providers. The local provider is restricted to user-owned files.

### Sync
AniList OAuth and list mutations are isolated from the UI. Tokens are stored through the operating system credential store.

### Reliability
Memory caching works without infrastructure. Redis can be enabled through configuration. Offline mode returns cached data rather than requiring a network call.

## Data flow

```text
TUI action
  -> service
  -> metadata/storage/provider/player adapter
  -> domain model
  -> TUI render
```

## Safety boundary

The provider layer is intended for authorized or user-owned media sources. The project does not implement DRM bypassing or unauthorized access to copyrighted streams.
