"""Ani-Watch package."""

from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("ani-watch")
except PackageNotFoundError:
    # Source checkouts can be imported before an editable install exists.
    __version__ = "0.2.0"
