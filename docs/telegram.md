# Telegram personal media

Ani-Watch can use a private Telegram channel as an authorized personal media source while keeping the anime catalog and episode metadata in AniList.

## Setup

1. Create a Telegram application at https://my.telegram.org/apps.
2. Keep the generated api_id and especially api_hash private.
3. Create a private Telegram channel and upload your authorized/user-owned media.
4. Configure Ani-Watch with:
   ani-watch telegram configure
5. The API hash is stored in the operating-system keyring. The MTProto session is stored in the platform data directory rather than the repository.
6. Log in once with:
   ani-watch telegram login
7. Check the connection with:
   ani-watch telegram status
   ani-watch telegram sync

## Exact AniList-to-Telegram mapping

The recommended caption format is:
anilist_id=123 episode=1

You can also combine the mapping with a normal title or description:
My personal video
anilist_id=123 episode=1

Ani-Watch first prefers an explicit AniList ID plus episode mapping. As a convenience, it can fall back to matching the AniList title plus an episode label in the Telegram filename or caption.

Example filename:
Naruto - Episode 01.mp4

## Playback behavior

Selecting Play from the normal AniList-backed episode screen continues to use the existing provider resolver. When Telegram is configured and the local provider does not resolve the episode, the Telegram provider returns a local HTTP URL backed by a Range-capable gateway.

The gateway requests Telegram media in chunks as VLC asks for them. It does not first download the complete file to disk. Seeking works through HTTP byte ranges when VLC requests a new range.

This integration is intended for media you own or are otherwise authorized to access. It does not bypass DRM or extract unauthorized copyrighted streams.

## Troubleshooting

- Telegram API ID is not configured: run ani-watch telegram configure.
- Telegram account is not authorized: run ani-watch telegram login.
- No Telegram media matched: add an exact anilist_id=<id> episode=<number> caption.
- VLC cannot start playback: verify VLC/libVLC is installed and the media container and codec are supported by VLC.
