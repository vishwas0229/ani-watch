"""Factories for configured metadata and cache adapters."""

from ani_watch.auth.anilist import TokenStore
from ani_watch.cache.redis import RedisCache
from ani_watch.config.store import SettingsStore

from .cache import CachedAniListMetadataService
from .client import AniListClient
from .service import AniListMetadataService


def build_metadata_service():
    """Build the metadata service from persisted user settings."""
    settings = SettingsStore().load()
    client = AniListClient(
        url=settings.anilist.graphql_url,
        access_token=TokenStore().load(),
        timeout=settings.providers.timeout_seconds,
    )
    service = AniListMetadataService(client)
    if settings.cache.enabled and settings.cache.url:
        return CachedAniListMetadataService(
            service,
            RedisCache(settings.cache.url, settings.cache.ttl_seconds),
        )
    return service
