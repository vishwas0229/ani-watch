# Ani-Watch Architecture

## Layering

Ani-Watch is structured around explicit package boundaries:

- **domain** — framework-independent application concepts and value objects.
- **services** — application orchestration and dependency-inversion contracts.
- **metadata** — external anime metadata integrations such as AniList.
- **storage** — persistence and repository adapters.
- **player** — media-player adapters such as VLC/libVLC.
- **providers** — content-source/provider and resolver adapters.
- **tui** — Textual presentation layer.
- **infra** — cross-cutting infrastructure integrations.

The dependency direction is intentionally kept inward:

`tui / cli → services → domain`

External integrations should be accessed through service contracts or adapter boundaries rather than leaking infrastructure details into the domain.
