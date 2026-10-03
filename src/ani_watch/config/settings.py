"""Typed application configuration defaults."""

from pydantic import BaseModel, Field


class PlaybackSettings(BaseModel):
    """Playback-related preferences."""

    quality: str = "1080p"
    audio: str = "default"
    auto_next: bool = True
    skip_intro: bool = False
    skip_outro: bool = False


class UISettings(BaseModel):
    """Terminal UI preferences."""

    theme: str = "midnight"
    episode_layout: str = "grid"
    density: str = "normal"


class AppSettings(BaseModel):
    """Top-level application settings."""

    playback: PlaybackSettings = Field(default_factory=PlaybackSettings)
    ui: UISettings = Field(default_factory=UISettings)
