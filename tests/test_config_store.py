import os
from pathlib import Path

import pytest

from ani_watch.config.settings import AppSettings
from ani_watch.config.store import SettingsStore
from ani_watch.domain.errors import ConfigurationError


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
    settings.ui.theme = "mono"

    store.save(settings)
    loaded = store.load()

    assert loaded.playback.quality == "720p"
    assert loaded.playback.auto_next is False
    assert loaded.ui.theme == "mono"


def test_invalid_values_are_rejected() -> None:
    with pytest.raises(ValueError):
        AppSettings(ui={"theme": "dracula"})


def test_invalid_persisted_config_raises_controlled_error(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        '[ui]\ntheme = "dracula"\n',
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="Invalid Ani-Watch configuration"):
        SettingsStore(path).load()


def test_saved_file_is_restricted_on_posix(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    SettingsStore(path).save(AppSettings())

    if os.name == "posix":
        assert path.stat().st_mode & 0o777 == 0o600
