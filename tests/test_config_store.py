from pathlib import Path

from ani_watch.config.settings import AppSettings
from ani_watch.config.store import SettingsStore


def test_missing_config_returns_defaults(tmp_path: Path) -> None:
    settings = SettingsStore(tmp_path / "config.toml").load()

    assert settings.playback.auto_next is True
    assert settings.ui.theme == "midnight"


def test_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "config.toml"
    store = SettingsStore(path)

    settings = AppSettings()
    settings.playback.quality = "720p"
    settings.playback.auto_next = False
    settings.ui.theme = "dracula"

    store.save(settings)
    loaded = store.load()

    assert loaded.playback.quality == "720p"
    assert loaded.playback.auto_next is False
    assert loaded.ui.theme == "dracula"


def test_saved_file_is_restricted_on_posix(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    store = SettingsStore(path)
    store.save(AppSettings())

    if path.stat().st_mode & 0o777 != 0o600:
        raise AssertionError("configuration file must be owner-readable on POSIX")
