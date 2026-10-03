import logging
from pathlib import Path

from ani_watch.domain.errors import AniWatchError, PlaybackError
from ani_watch.infra.logging import configure_logging, get_logger


def test_exception_hierarchy() -> None:
    error = PlaybackError("player unavailable")

    assert isinstance(error, AniWatchError)
    assert str(error) == "player unavailable"


def test_configure_logging_writes_file(tmp_path: Path) -> None:
    log_file = tmp_path / "logs" / "ani-watch.log"
    logger = configure_logging(level="DEBUG", log_file=log_file)

    logger.info("test message")

    for handler in logger.handlers:
        handler.flush()

    assert log_file.exists()
    assert "test message" in log_file.read_text(encoding="utf-8")


def test_get_logger_returns_named_logger() -> None:
    logger = get_logger("ani_watch.test")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "ani_watch.test"
