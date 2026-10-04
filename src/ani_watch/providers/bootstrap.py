"""Provider bootstrap helpers."""

from pathlib import Path

from ani_watch.config.settings import AppSettings
from ani_watch.domain.errors import ConfigurationError
from ani_watch.providers.local import LocalFileProvider
from ani_watch.providers.online import DirectUrlProvider
from ani_watch.providers.registry import ProviderRegistry
from ani_watch.providers.streamlink import StreamlinkProvider


def build_provider_registry(settings: AppSettings) -> ProviderRegistry:
    """Build configured providers in deterministic fallback order."""
    registry = ProviderRegistry()

    if not settings.provider_enabled:
        return registry

    local_root: Path | None = None
    if settings.local_media_root:
        local_root = Path(settings.local_media_root)
        if not local_root.exists():
            raise ConfigurationError("Configured local media root does not exist.")

    if settings.playback.local_first and local_root is not None:
        registry.register(LocalFileProvider(local_root))

    if settings.streamlink_url_template:
        try:
            registry.register(StreamlinkProvider(settings.streamlink_url_template))
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc

    if settings.online_media_url_template:
        try:
            registry.register(DirectUrlProvider(settings.online_media_url_template))
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc

    if not settings.playback.local_first and local_root is not None:
        registry.register(LocalFileProvider(local_root))

    return registry
