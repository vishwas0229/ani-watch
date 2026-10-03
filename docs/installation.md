# Installation

Ani-Watch runs only inside the repository-managed Conda environment.

## Requirements

- Conda (Miniconda or Anaconda)
- Python 3.12+
- VLC installed and available to libVLC for playback
- PostgreSQL is supported for shared/persistent deployments
- Redis is optional for distributed caching

## Create the environment

From the repository root:

```bash
conda env create -f environment.yml
conda activate ani-watch
python -m pip install -e ".[dev]"
```

## Run

```bash
python main.py
```

## Platform installers

Linux:

```bash
bash scripts/install-linux.sh
```

macOS:

```bash
bash scripts/install-macos.sh
```

Windows PowerShell:

```powershell
./scripts/install-windows.ps1
```
