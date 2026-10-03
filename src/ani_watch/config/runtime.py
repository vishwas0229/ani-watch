"""Runtime environment validation for Ani-Watch."""

from __future__ import annotations

import os


class CondaEnvironmentError(RuntimeError):
    """Raised when Ani-Watch is started outside an active Conda environment."""


def require_conda_environment() -> None:
    """Require Ani-Watch to run from an activated Conda environment."""
    if os.environ.get("CONDA_PREFIX"):
        return

    raise CondaEnvironmentError(
        "Ani-Watch requires an active Conda environment. "
        "Create the project environment first with: "
        "'conda env create -f environment.yml' and "
        "'conda activate ani-watch'."
    )
