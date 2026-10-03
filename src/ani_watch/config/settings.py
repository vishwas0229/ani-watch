"""Typed application configuration."""

from pydantic import BaseModel, Field


class PlaybackSettings(BaseModel):
    """Playback-related preferences."""

    quality: str = "1080p"
    audio: str = "default"
    subtitle: str = "default"
    auto_next: bool = True
    skip_intro: bool = False
    skip_outro: bool = False
    local_first: bool = True
    volume: int = Field(default=80, ge=0, le=100)
    intro_seconds: int = Field(default=0, ge=0)
    outro_seconds: int = Field(default=0, ge=0)


class UISettings(BaseModel):
    """Terminal UI preferences."""

    theme: str = "midnight"
    episode_layout: str = "list"
    density: str = "normal"


class DatabaseSettings(BaseModel):
    """PostgreSQL connection settings."""

    url: str = "postgresql+psycopg://ani_watch:ani_watch@localhost:5432/ani_watch"


class AniListSettings(BaseModel):
    """AniList API and OAuth configuration."""

    graphql_url: str = "https://graphql.anilist.co"
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None


class CacheSettings(BaseModel):
    """Redis cache configuration."""

    url: str | None = None
    enabled: bool = False
    ttl_seconds: int = Field(default=900, ge=30)


class ProviderSettings(BaseModel):
    """Provider selection and reliability settings."""

    enabled: list[str] = Field(default_factory=lambda: ["local"])
    timeout_seconds: float = Field(default=15.0, gt=0)
    failure_threshold: int = Field(default=3, ge=1)
    recovery_seconds: int = Field(default=60, ge=1)
    local_media_dirs: list[str] = Field(default_factory=list)


class AppSettings(BaseModel):
    """Top-level application settings."""

    playback: PlaybackSettings = Field(default_factory=PlaybackSettings)
    ui: UISettings = Field(default_factory=UISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    anilist: AniListSettings = Field(default_factory=AniListSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    providers: ProviderSettings = Field(default_factory=ProviderSettings)
