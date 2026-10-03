"""Provider bootstrap helpers."""

from pathlib import Path

from ani_watch.config.settings import AppSettings
from ani_watch.domain.models import AnimeRef
from ani_watch.domain.errors import ConfigurationError
from ani_watch.providers.local import LocalFileProvider
from ani_watch.providers.registry import ProviderRegistry


def build_provider_registry(settings: AppSettings) -> ProviderRegistry:
    """Build configured providers in deterministic fallback order."""
    registry = ProviderRegistry()
    if not settings.provider_enabled:
        return registry
    if settings.local_media_root:
        root = Path(settings.local_media_root)
        if root.exists():
            registry.register(LocalFileProvider(root))
        elif not root.parent.exists():
            raise ConfigurationError("Configured local media root does not exist.")
    return registry
