import os

import pytest

from typer.testing import CliRunner

from ani_watch.cli.main import app


def test_cli_doctor_requires_conda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code != 0
    assert "active Conda environment" in result.stdout


def test_cli_doctor_in_conda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONDA_PREFIX", os.getcwd())
    result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Ani-Watch environment: Conda" in result.stdout
