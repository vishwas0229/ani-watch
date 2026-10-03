"""Domain model used by the anime details surface."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnimeDetails:
    """Provider-neutral metadata required to render one anime."""

    anilist_id: int
    title: str
    native_title: str | None = None
    description: str | None = None
    status: str | None = None
    episodes: int | None = None
    score: float | None = None
    genres: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    season: str | None = None
    year: int | None = None
    format: str | None = None
    duration_minutes: int | None = None
    cover_url: str | None = None
    site_url: str | None = None
    is_favorite: bool = False
