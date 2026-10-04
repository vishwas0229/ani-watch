from ani_watch.domain.models import EpisodeItem
from ani_watch.providers.contracts import MediaCandidate
from ani_watch.providers.registry import ProviderRegistry
from ani_watch.tui.app import AniWatchApp
from ani_watch.tui.screens.episodes import EpisodeScreen


class FakeOnlineProvider:
    name = "online"

    async def available(self, anime, episode) -> bool:
        return True

    async def resolve(self, anime, episode, *, quality=None) -> MediaCandidate:
        return MediaCandidate(
            uri="https://media.example/episode.m3u8",
            provider="online",
            quality=quality,
        )


class FakeStreamlinkProvider:
    name = "streamlink"

    async def available(self, anime, episode) -> bool:
        return True

    async def resolve(self, anime, episode, *, quality=None) -> MediaCandidate:
        return MediaCandidate(
            uri="https://media.example/streamlink-episode.m3u8",
            provider="streamlink",
            quality=quality,
        )


class FakeSession:
    def __init__(self, resolver) -> None:
        self.resolver = resolver
        self.provider_names: list[str | None] = []
        self.candidates: list[MediaCandidate] = []

    async def start(
        self,
        anime,
        episode,
        *,
        episode_index=0,
        total_episodes=1,
        provider_name=None,
    ):
        self.provider_names.append(provider_name)
        return MediaCandidate(
            uri="https://media.example/episode.m3u8",
            provider=provider_name or "online",
            quality="1080p",
        )

    def start_candidate(
        self,
        anime,
        episode,
        candidate,
        *,
        episode_index=0,
        total_episodes=1,
    ):
        self.candidates.append(candidate)
        return candidate

    def tick(self) -> bool:
        return False

    def next_episode_index(self, total: int):
        return None

    def stop(self) -> None:
        return

    def close(self) -> None:
        return


async def test_watch_online_uses_direct_provider_when_configured() -> None:
    resolver = type(
        "Resolver",
        (),
        {"providers": ProviderRegistry([FakeOnlineProvider()])},
    )()
    session = FakeSession(resolver)
    app = AniWatchApp(provider_resolver=resolver, playback_session=session)

    async with app.run_test() as pilot:
        await app.push_screen(
            EpisodeScreen(
                "Sample Anime",
                (EpisodeItem(number=1, title="Episode 1"),),
                anime_id=100,
                playback_session=session,
            )
        )
        await pilot.click("#watch-online")
        await pilot.pause()

        assert session.provider_names == ["online"]
        assert "Playing Episode 1 via online" in str(
            app.screen.query_one("#episode-status").content
        )


async def test_watch_online_prefers_streamlink_when_both_are_configured() -> None:
    resolver = type(
        "Resolver",
        (),
        {
            "providers": ProviderRegistry(
                [FakeOnlineProvider(), FakeStreamlinkProvider()]
            )
        },
    )()
    session = FakeSession(resolver)
    app = AniWatchApp(provider_resolver=resolver, playback_session=session)

    async with app.run_test() as pilot:
        await app.push_screen(
            EpisodeScreen(
                "Sample Anime",
                (EpisodeItem(number=1, title="Episode 1"),),
                anime_id=100,
                playback_session=session,
            )
        )
        await pilot.click("#watch-online")
        await pilot.pause()

        assert session.provider_names == ["streamlink"]
        assert "Playing Episode 1 via streamlink" in str(
            app.screen.query_one("#episode-status").content
        )


async def test_watch_online_auto_resolves_anilist_link_with_streamlink(monkeypatch) -> None:
    class FakeMetadataService:
        async def streaming_episodes(self, anime_id: int):
            assert anime_id == 100
            return {
                1: [
                    {
                        "title": "Episode 1",
                        "url": "https://supported.example/watch/episode-1",
                        "site": "Supported",
                    }
                ]
            }

    async def fake_resolve_url(source_url: str, *, quality: str | None = None):
        assert source_url == "https://supported.example/watch/episode-1"
        assert quality == "1080p"
        return MediaCandidate(
            uri="https://cdn.example/episode-1.m3u8",
            provider="streamlink",
            quality="1080p",
        )

    monkeypatch.setattr(
        "ani_watch.tui.screens.episodes.StreamlinkProvider.resolve_url",
        fake_resolve_url,
    )
    resolver = type("Resolver", (), {"providers": ProviderRegistry()})()
    session = FakeSession(resolver)
    app = AniWatchApp(provider_resolver=resolver, playback_session=session)

    async with app.run_test() as pilot:
        await app.push_screen(
            EpisodeScreen(
                "Sample Anime",
                (EpisodeItem(number=1, title="Episode 1"),),
                anime_id=100,
                playback_session=session,
                metadata_service=FakeMetadataService(),
            )
        )
        await pilot.click("#watch-online")
        await pilot.pause()

        assert session.candidates == [
            MediaCandidate(
                uri="https://cdn.example/episode-1.m3u8",
                provider="streamlink",
                quality="1080p",
            )
        ]
        assert "Playing Episode 1 via Streamlink in VLC" in str(
            app.screen.query_one("#episode-status").content
        )

