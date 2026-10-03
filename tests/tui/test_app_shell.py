from ani_watch.tui.app import AniWatchApp


def test_app_shell_metadata() -> None:
    assert AniWatchApp.TITLE == "Ani-Watch"
    assert any(binding[0] == "q" for binding in AniWatchApp.BINDINGS)


def test_app_can_be_constructed() -> None:
    app = AniWatchApp()
    assert app.title == "Ani-Watch"
