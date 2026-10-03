# Providers and plugins

Providers are adapters behind a small protocol:

- check whether an anime/episode is available
- resolve a playable URI for authorized or user-owned media
- optionally honor a quality preference

The built-in local provider searches the configured local_media_root.

ProviderRegistry controls deterministic order. ProviderResolver tries providers in order, records health, applies the circuit breaker and falls back after a failure.

To add a provider, implement src/ani_watch/providers/contracts.py, add provider-specific parsing/network logic in its own module, and register it in the application bootstrap layer. Keep provider details out of the TUI and domain.

The project intentionally does not implement DRM bypassing or unauthorized copyrighted-stream access.
