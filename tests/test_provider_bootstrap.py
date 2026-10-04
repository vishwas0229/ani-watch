from pathlib import Path

from ani_watch.config.settings import AppSettings
from ani_watch.providers.bootstrap import build_provider_registry


def test_provider_bootstrap_registers_existing_local_root(tmp_path: Path) -> None:
    settings = AppSettings(local_media_root=tmp_path)
    registry = build_provider_registry(settings)
    assert registry.names == ("local",)


def test_provider_bootstrap_honors_disabled_flag(tmp_path: Path) -> None:
    settings = AppSettings(local_media_root=tmp_path, provider_enabled=False)
    registry = build_provider_registry(settings)
    assert registry.names == ()


def test_provider_bootstrap_registers_telegram_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        "ani_watch.auth.telegram.keyring.get_password",
        lambda service, key: "test-api-hash",
    )
    settings = AppSettings(
        telegram_api_id=123456,
        telegram_channel="-1001234567890",
    )

    registry = build_provider_registry(settings)

    assert "telegram" in registry.names
