from pathlib import Path  # noqa: I001


ROOT = Path(__file__).parents[1]


def test_posix_installers_update_existing_env_and_verify_runtime() -> None:
    for name in ("install-linux.sh", "install-macos.sh"):
        text = (ROOT / "scripts" / name).read_text(encoding="utf-8")

        assert "conda env update -n" in text
        assert "conda env create -f environment.yml" in text
        assert "import ani_watch" in text
        assert "vlc.Instance" in text
        assert "VLC/libVLC" in text


def test_windows_installer_updates_existing_env_and_verifies_runtime() -> None:
    text = (ROOT / "scripts" / "install-windows.ps1").read_text(encoding="utf-8")

    assert "conda env update -n $envName" in text
    assert "conda env create -f environment.yml" in text
    assert "import ani_watch" in text
    assert "vlc.Instance" in text
    assert "VLC/libVLC" in text


def test_installers_are_idempotent_after_an_existing_environment_is_found() -> None:
    scripts = (
        ROOT / "scripts" / "install-linux.sh",
        ROOT / "scripts" / "install-macos.sh",
        ROOT / "scripts" / "install-windows.ps1",
    )
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        assert "conda env update" in text
