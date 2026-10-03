from ani_watch.config.settings import DatabaseSettings
from ani_watch.domain.details import AnimeDetails
from ani_watch.storage.db import Database
from ani_watch.storage.service import LibraryService


def test_library_service_round_trip() -> None:
    database = Database(DatabaseSettings(url="sqlite+pysqlite:///:memory:"))
    database.create_schema()
    service = LibraryService(database)

    anime = AnimeDetails(
        anilist_id=10,
        title="Example",
        episodes=12,
        genres=("Drama",),
    )
    service.save_anime_and_episodes(
        anime,
        [
            __import__("ani_watch.domain.episode", fromlist=["EpisodeItem"]).EpisodeItem(
                number=1,
                anime_id=10,
                title="One",
            )
        ],
    )
    service.set_favorite(anime, True)
    service.record_progress(anime, 1, 30, 60)

    assert service.favorites()[0].title == "Example"
    assert service.history()[0].episode_number == 1
    assert service.statistics().favorite_count == 1

    database.dispose()
