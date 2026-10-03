#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v conda >/dev/null 2>&1 || {
  echo "Conda is required. Install Miniconda or Anaconda first." >&2
  exit 1
}

conda env create -f environment.yml || conda env update -f environment.yml --prune
echo "Ani-Watch installed. Activate with: conda activate ani-watch"
