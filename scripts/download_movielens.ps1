param([string]$Dataset = "bhatvikas/movielens-100k-dataset")

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$dataRoot = Join-Path $repoRoot "data"
$rawRoot = Join-Path $dataRoot "raw"

function Get-PythonCommand {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }

    throw "Python is not available in PATH. Activate the virtual environment first or install Python 3."
}

$pythonCommand = Get-PythonCommand

New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
New-Item -ItemType Directory -Path $rawRoot -Force | Out-Null

if (-not (Test-Path "$HOME/.kaggle/kaggle.json")) {
    Write-Warning "Kaggle credentials were not found in $HOME/.kaggle/kaggle.json. Create a Kaggle API token before running this script."
}

& $pythonCommand -m pip install --upgrade kaggle
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install the Kaggle CLI."
}

$kaggleCommand = Get-Command kaggle -ErrorAction SilentlyContinue
if ($null -ne $kaggleCommand) {
    & $kaggleCommand.Source datasets download -d $Dataset -p $dataRoot
} else {
    & $pythonCommand -m kaggle datasets download -d $Dataset -p $dataRoot
}

if ($LASTEXITCODE -ne 0) {
    throw "Kaggle download failed. Verify the dataset name and your Kaggle API credentials."
}

$archive = Get-ChildItem -LiteralPath $dataRoot -Filter "*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $archive) {
    throw "Kaggle download did not create a ZIP archive in '$dataRoot'."
}

Expand-Archive -LiteralPath $archive.FullName -DestinationPath $rawRoot -Force
Remove-Item -LiteralPath $archive.FullName -Force

$expectedFile = Join-Path $rawRoot "ml-100k/u.data"
if (-not (Test-Path $expectedFile)) {
    throw "Unexpected archive layout: expected '$expectedFile'"
}

Write-Host "MovieLens 100K is ready in '$rawRoot'."
