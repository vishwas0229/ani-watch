from pathlib import Path

import pytest

from ani_watch.domain.models import AnimeRef
from ani_watch.providers.local import LocalProvider


@pytest.mark.asyncio
async def test_local_provider_discovers_episode_files(tmp_path: Path) -> None:
    anime_dir = tmp_path / "media"
    anime_dir.mkdir()
    (anime_dir / "Sample Anime - 01.mkv").touch()
    (anime_dir / "Sample Anime S01E02.mp4").touch()
    (anime_dir / "Other Show - 01.mkv").touch()

    provider = LocalProvider([str(anime_dir)])
    episodes = await provider.episodes(AnimeRef(1, "Sample Anime"))

    assert [episode.number for episode in episodes] == [1, 2]
    assert all(episode.source_uri for episode in episodes)
