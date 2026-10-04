$ErrorActionPreference = "Stop"

$envName = "ani-watch"

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "Conda is required. Install Miniconda or Anaconda first."
}

$envExists = conda env list | Select-String -Quiet "^\s*$envName\s"
if ($envExists) {
    conda env update -n $envName -f environment.yml --prune
} else {
    conda env create -f environment.yml
}

conda run -n $envName python -m pip install -e ".[dev]"
conda run -n $envName python -c "import ani_watch; print('Ani-Watch import: OK')"

conda run -n $envName python -c "import vlc; instance = vlc.Instance('--intf=dummy'); assert instance is not None; instance.release()"
if ($LASTEXITCODE -ne 0) {
    throw "VLC/libVLC is not available. Install VLC from VideoLAN and run this installer again."
}

Write-Host "VLC/libVLC: OK"
Write-Host "Ani-Watch installed in Conda environment '$envName'."
Write-Host "Activate it with: conda activate $envName"
