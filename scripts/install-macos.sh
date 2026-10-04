#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="ani-watch"

if ! command -v conda >/dev/null 2>&1; then
  echo "Conda is required. Install Miniconda/Anaconda first." >&2
  exit 1
fi

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda env update -n "$ENV_NAME" -f environment.yml --prune
else
  conda env create -f environment.yml
fi

conda run -n "$ENV_NAME" python -m pip install -e ".[dev]"
conda run -n "$ENV_NAME" python -c 'import ani_watch; print("Ani-Watch import: OK")'

if ! conda run -n "$ENV_NAME" python -c 'import vlc; instance = vlc.Instance("--intf=dummy"); assert instance is not None; instance.release()'; then
  echo "VLC/libVLC is not available to the Ani-Watch Conda environment." >&2
  echo "Install VLC (for example with: brew install --cask vlc) and run this installer again." >&2
  exit 1
fi

echo "VLC/libVLC: OK"
echo "Ani-Watch installed in Conda environment '$ENV_NAME'."
echo "Activate it with: conda activate $ENV_NAME"
