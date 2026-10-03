"""Typed application configuration."""

from pathlib import Path
from typing import Literal

from platformdirs import user_data_path
from pydantic import BaseModel, Field

QualityMode = Literal["1080p", "720p", "480p", "auto"]
AudioMode = Literal["default"]
SubtitleMode = Literal["default"]
UITheme = Literal["midnight", "mono", "high-contrast"]
UIDensity = Literal["compact", "normal", "comfortable"]


class PlaybackSettings(BaseModel):
    quality: QualityMode = "1080p"
    audio: AudioMode = "default"
    subtitle: SubtitleMode = "default"
    auto_next: bool = True
    skip_intro: bool = False
    skip_outro: bool = False
    local_first: bool = True
    volume: int = Field(default=80, ge=0, le=200)


class UISettings(BaseModel):
    theme: UITheme = "midnight"
    density: UIDensity = "normal"
    responsive: bool = True


class NetworkSettings(BaseModel):
    timeout_seconds: float = Field(default=10.0, gt=0)
    retries: int = Field(default=3, ge=0, le=10)
    offline_mode: bool = False


class AppSettings(BaseModel):
    playback: PlaybackSettings = Field(default_factory=PlaybackSettings)
    ui: UISettings = Field(default_factory=UISettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    database_url: str = "sqlite:///" + str(user_data_path("ani-watch") / "ani-watch.db")
    redis_url: str | None = None
    anilist_client_id: str | None = None
    anilist_client_secret: str | None = None
    anilist_redirect_uri: str = "http://localhost:8080/callback"
    local_media_root: Path | None = None
    provider_enabled: bool = True
