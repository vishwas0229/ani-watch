# Changelog

## 0.2.0 - 2026-10-03

### Added
- Conda-only runtime and reproducible environment definition.
- Textual home, search, details, episodes, history, favorites, library, and settings screens.
- AniList GraphQL metadata client with retries, timeout handling and rate-limit errors.
- SQLite/PostgreSQL persistence via SQLAlchemy 2 with an initial Alembic migration.
- VLC/libVLC playback adapter and playback intelligence services.
- Provider registry, local-file provider, fallback resolver, health tracking and circuit breaker.
- AniList OAuth helpers and account synchronization services.
- Memory/Redis caching and offline/degraded metadata handling.
- Cross-platform Conda installation scripts and release automation.
