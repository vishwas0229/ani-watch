"""Persistent TOML configuration storage."""

from __future__ import annotations

import os
import tempfile
import tomllib
from pathlib import Path

import tomli_w
from platformdirs import user_config_path

from ani_watch.config.settings import AppSettings


class SettingsStore:
    """Load and persist validated application settings."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or user_config_path("ani-watch") / "config.toml"

    def load(self) -> AppSettings:
        """Load settings from disk, falling back to typed defaults."""
        if not self.path.exists():
            return AppSettings()

        with self.path.open("rb") as file:
            data = tomllib.load(file)

        return AppSettings.model_validate(data)

    def save(self, settings: AppSettings) -> None:
        """Atomically persist settings as TOML."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = tomli_w.dumps(settings.model_dump(mode="json", exclude_none=True))

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)

        temporary_path.replace(self.path)

        if os.name == "posix":
            self.path.chmod(0o600)
