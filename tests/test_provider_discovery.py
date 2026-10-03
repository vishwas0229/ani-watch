from pathlib import Path

from ani_watch.config.settings import AppSettings
from ani_watch.providers.discovery import discover_providers


def test_provider_discovery_uses_configured_local_provider(tmp_path: Path) -> None:
    settings = AppSettings(local_media_root=tmp_path)
    registry = discover_providers(settings)
    assert "local" in registry.names
