import pytest

from ani_watch.config.runtime import CondaEnvironmentError, require_conda_environment


def test_runtime_requires_conda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CONDA_PREFIX", raising=False)

    with pytest.raises(CondaEnvironmentError, match="active Conda environment"):
        require_conda_environment()


def test_runtime_accepts_active_conda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONDA_PREFIX", "/opt/conda/envs/ani-watch")

    require_conda_environment()
