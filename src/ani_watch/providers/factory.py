"""Factories for configured provider adapters."""

from ani_watch.config.settings import ProviderSettings
from .local import LocalProvider
from .registry import ProviderRegistry


def build_provider_registry(settings: ProviderSettings) -> ProviderRegistry:
    """Build the configured provider registry."""
    providers = []
    names = tuple(settings.enabled)

    if "local" in names:
        providers.append(
            LocalProvider(
                settings.local_media_dirs,
                failure_threshold=settings.failure_threshold,
                recovery_seconds=settings.recovery_seconds,
            )
        )
    return ProviderRegistry(providers)
