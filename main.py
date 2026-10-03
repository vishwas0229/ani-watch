"""Repository-level launcher for Ani-Watch.

The application logic remains inside the installable ani_watch package.
This file is the primary executable entry point for a source checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_src() -> None:
    """Make the src-layout package importable from a source checkout."""
    src_dir = Path(__file__).resolve().parent / "src"
    src_path = str(src_dir)

    if src_dir.is_dir() and src_path not in sys.path:
        sys.path.insert(0, src_path)


def main() -> None:
    """Launch the Ani-Watch CLI."""
    _bootstrap_src()

    from ani_watch.cli.main import app

    app()


if __name__ == "__main__":
    main()
