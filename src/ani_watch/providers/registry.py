"""Provider registry and discovery helpers."""

from collections.abc import Iterable

from ani_watch.providers.contracts import Provider


class ProviderRegistry:
    """Register providers and expose deterministic lookup order."""

    def __init__(self, providers: Iterable[Provider] = ()) -> None:
        self._providers: dict[str, Provider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: Provider) -> None:
        key = provider.name.strip().lower()
        if not key:
            raise ValueError("Provider name cannot be empty.")
        self._providers[key] = provider

    def remove(self, name: str) -> None:
        self._providers.pop(name.strip().lower(), None)

    def get(self, name: str) -> Provider | None:
        return self._providers.get(name.strip().lower())

    def ordered(self) -> tuple[Provider, ...]:
        return tuple(self._providers.values())

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._providers)
