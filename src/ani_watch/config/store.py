"""Persistent TOML configuration storage."""

from __future__ import annotations

import os
import tempfile
import tomllib
from pathlib import Path

import tomli_w
from platformdirs import user_config_path
from pydantic import ValidationError

from ani_watch.config.settings import AppSettings
from ani_watch.domain.errors import ConfigurationError


class SettingsStore:
    """Load and persist validated application settings."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or user_config_path("ani-watch") / "config.toml"

    def load(self) -> AppSettings:
        """Load settings and convert invalid files into a safe application error."""
        if not self.path.exists():
            return AppSettings()

        try:
            with self.path.open("rb") as file:
                data = tomllib.load(file)
            return AppSettings.model_validate(data)
        except (OSError, tomllib.TOMLDecodeError, ValidationError) as exc:
            raise ConfigurationError(
                f"Invalid Ani-Watch configuration at {self.path}. "
                "Edit or remove the file and restart Ani-Watch to restore defaults."
            ) from exc

    def save(self, settings: AppSettings) -> None:
        """Atomically persist validated application settings as TOML."""
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
