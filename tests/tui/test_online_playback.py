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


class FakeSession:
    def __init__(self, resolver) -> None:
        self.resolver = resolver
        self.provider_names: list[str | None] = []

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
            provider="online",
            quality="1080p",
        )

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
