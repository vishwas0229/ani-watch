$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

conda env create -f environment.yml
if ($LASTEXITCODE -ne 0) {
    conda env update -f environment.yml --prune
}

Write-Host "Ani-Watch installed. Activate with: conda activate ani-watch"
