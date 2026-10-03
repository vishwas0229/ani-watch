"""Application-level exception hierarchy."""

class AniWatchError(Exception):
    """Base exception for expected Ani-Watch failures."""


class ConfigurationError(AniWatchError):
    """Configuration could not be loaded or validated."""


class MetadataError(AniWatchError):
    """Anime metadata could not be retrieved or parsed."""


class PlaybackError(AniWatchError):
    """Media playback could not be started or controlled."""


class ProviderError(AniWatchError):
    """A provider failed to fulfill a request."""


class StorageError(AniWatchError):
    """Persistent storage could not fulfill a request."""
