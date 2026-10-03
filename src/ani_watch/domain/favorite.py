"""Domain model for saved anime favorites."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FavoriteAnime:
    """Provider-neutral favorite entry consumed by the TUI."""

    anime_id: int
    title: str
    native_title: str | None = None
    status: str | None = None
    episodes: int | None = None
    score: float | None = None
    genres: tuple[str, ...] = ()
