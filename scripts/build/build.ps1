# Build PyInstaller one-folder dist under repo/dist/cursor-usage/
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

& $python -m pip install -e ".[build]" -q
& $python -m PyInstaller --noconfirm --clean (Join-Path $PSScriptRoot "cursor-usage.spec")

Write-Host "Build output: $(Join-Path $RepoRoot 'dist\cursor-usage')"
