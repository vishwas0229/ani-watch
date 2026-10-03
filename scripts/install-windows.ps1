$ErrorActionPreference = "Stop"

$envName = "ani-watch"

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "Conda is required. Install Miniconda or Anaconda first."
}

conda env list | Select-String -Quiet "^$envName\s"
if (-not $?) {
    conda env create -f environment.yml
}

conda run -n $envName python -m pip install -e ".[dev]"
Write-Host "Ani-Watch installed in Conda environment '$envName'."
Write-Host "Activate it with: conda activate $envName"
