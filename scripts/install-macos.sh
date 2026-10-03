#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="ani-watch"

if ! command -v conda >/dev/null 2>&1; then
  echo "Conda is required. Install Miniconda/Anaconda first." >&2
  exit 1
fi

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda env create -f environment.yml
fi

conda run -n "$ENV_NAME" python -m pip install -e ".[dev]"
echo "Ani-Watch installed in Conda environment '$ENV_NAME'."
echo "Activate it with: conda activate $ENV_NAME"
