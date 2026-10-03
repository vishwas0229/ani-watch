import importlib


def test_core_packages_are_importable() -> None:
    packages = (
        "ani_watch.domain",
        "ani_watch.services",
        "ani_watch.metadata",
        "ani_watch.storage",
        "ani_watch.player",
        "ani_watch.providers",
        "ani_watch.tui",
        "ani_watch.infra",
    )

    for package in packages:
        assert importlib.import_module(package) is not None


def test_domain_reference_objects_are_stable() -> None:
    from ani_watch.domain.models import AnimeRef, EpisodeRef

    anime = AnimeRef(anilist_id=100, title="Example")
    episode = EpisodeRef(anime_id=100, number=1)

    assert anime.anilist_id == 100
    assert episode.number == 1
