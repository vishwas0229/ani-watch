"""Application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platformdirs import user_log_path

DEFAULT_LOGGER_NAME = "ani_watch"
DEFAULT_LOG_FILE = user_log_path("ani-watch") / "ani-watch.log"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a namespaced application logger."""
    return logging.getLogger(name or DEFAULT_LOGGER_NAME)


def configure_logging(
    level: str = "INFO",
    log_file: Path | None = DEFAULT_LOG_FILE,
) -> logging.Logger:
    """Configure console logging and an optional rotating log file.

    Existing Ani-Watch handlers are replaced so repeated setup calls do not
    duplicate log records.
    """
    logger = get_logger()
    logger.setLevel(level.upper())
    logger.propagate = False

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            path,
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.debug("Logging configured at %s", level.upper())
    return logger
