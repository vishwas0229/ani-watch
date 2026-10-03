"""Provider discovery helpers."""

from __future__ import annotations

from pathlib import Path

from ani_watch.config.settings import AppSettings
from ani_watch.providers.bootstrap import build_provider_registry
from ani_watch.providers.registry import ProviderRegistry


def discover_providers(settings: AppSettings) -> ProviderRegistry:
    """Discover built-in providers using current application configuration."""
    registry = build_provider_registry(settings)

    if settings.local_media_root:
        path = Path(settings.local_media_root)
        if path.exists() and "local" not in registry.names:
            from ani_watch.providers.local import LocalFileProvider

            registry.register(LocalFileProvider(path))
    return registry
