from importlib.metadata import version

from ani_watch import __version__
from ani_watch.config.settings import AppSettings


def test_version_matches_package_metadata() -> None:
    assert __version__ == version("ani-watch")


def test_default_settings_are_valid() -> None:
    settings = AppSettings()
    assert settings.playback.auto_next is True
    assert settings.ui.theme == "midnight"
