"""Provider contracts and media resolver value objects."""

from dataclasses import dataclass
from typing import Protocol

from ani_watch.domain.models import AnimeRef, EpisodeRef


@dataclass(frozen=True, slots=True)
class MediaCandidate:
    """A playable media location supplied by a lawful provider."""

    uri: str
    provider: str
    quality: str | None = None
    audio: str | None = None
    subtitle: str | None = None


class Provider(Protocol):
    """Provider contract for episode discovery and resolution."""

    name: str

    async def available(self, anime: AnimeRef, episode: EpisodeRef) -> bool:
        """Return whether the provider can serve the requested episode."""

    async def resolve(
        self,
        anime: AnimeRef,
        episode: EpisodeRef,
        *,
        quality: str | None = None,
    ) -> MediaCandidate | None:
        """Resolve a provider-owned or user-owned playable media URI."""
