from ani_watch.domain.models import AnimeRef, EpisodeRef
from ani_watch.providers.local import LocalFileProvider


def test_local_provider_resolves_exact_title_before_slug(tmp_path) -> None:
    exact = tmp_path / "My Anime - 01.mp4"
    slug = tmp_path / "my-anime-01.mkv"
    (tmp_path / "nested").mkdir()
    nested_slug = tmp_path / "nested" / "my-anime-01.webm"

    exact.touch()
    slug.touch()
    nested_slug.touch()

    provider = LocalFileProvider(tmp_path)
    anime = AnimeRef(1, "My Anime")
    episode = EpisodeRef(1, 1)

    matches = provider._candidates(anime, episode)

    assert matches[0] == exact
    assert matches == [exact, slug, nested_slug]


def test_local_provider_deduplicates_overlapping_patterns(tmp_path) -> None:
    path = tmp_path / "my-anime-01.mp4"
    path.touch()

    provider = LocalFileProvider(tmp_path)
    provider.root = _OverlappingRoot(path)

    matches = provider._candidates(
        AnimeRef(1, "My Anime"),
        EpisodeRef(1, 1),
    )

    assert matches == [path]


async def test_local_provider_skips_inaccessible_searches(tmp_path) -> None:
    path = tmp_path / "my-anime-01.mp4"
    path.touch()

    provider = LocalFileProvider(tmp_path)
    provider.root = _FailingRoot(path)

    assert await provider.available(AnimeRef(1, "My Anime"), EpisodeRef(1, 1))


class _OverlappingRoot:
    def __init__(self, path):
        self.path = path

    def rglob(self, pattern):
        return [self.path]


class _FailingRoot:
    def __init__(self, path):
        self.path = path

    def rglob(self, pattern):
        if pattern.startswith("My Anime"):
            raise PermissionError("denied")
        return [self.path]


def test_local_provider_accepts_unpadded_and_episode_filename_forms(tmp_path) -> None:
    path = tmp_path / "naruto-shippuden-1.mkv"
    path.touch()

    provider = LocalFileProvider(tmp_path)
    matches = provider._candidates(
        AnimeRef(20, "Naruto: Shippuden"),
        EpisodeRef(20, 1),
    )

    assert matches == [path]


def test_local_provider_supports_anime_folder_layout(tmp_path) -> None:
    folder = tmp_path / "Naruto Shippuden"
    folder.mkdir()
    path = folder / "Episode 01.mkv"
    path.touch()

    provider = LocalFileProvider(tmp_path)
    matches = provider._candidates(
        AnimeRef(21, "Naruto: Shippuden"),
        EpisodeRef(21, 1),
    )

    assert matches == [path]
