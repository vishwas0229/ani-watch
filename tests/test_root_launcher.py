from pathlib import Path


def test_root_launcher_exists_and_is_executable() -> None:
    launcher = Path(__file__).parents[1] / "main.py"

    content = launcher.read_text(encoding="utf-8")

    assert launcher.is_file()
    assert 'if __name__ == "__main__"' in content
    assert "from ani_watch.cli.main import app" in content
