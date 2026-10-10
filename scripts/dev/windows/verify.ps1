# Post-install smoke checks for Windows dev environment.
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$CursorUsage = Join-Path $Root ".venv\Scripts\cursor-usage.exe"

function Fail {
    param([string]$Message)
    Write-Error $Message
}

if (-not (Test-Path $VenvPython)) {
    Fail "Missing .venv. Run .\scripts\dev\windows\install.ps1 first."
}

$version = & $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$version -lt [version]"3.10") {
    Fail "Python 3.10+ required in .venv (found $version)."
}

Write-Host "OK  Python $version in .venv"

if (-not (Test-Path $CursorUsage)) {
    Fail "cursor-usage not installed in .venv."
}

& $CursorUsage --help | Out-Null
Write-Host "OK  cursor-usage --help"

& $VenvPython -m pytest
Write-Host "OK  pytest"

Write-Host ""
Write-Host "All checks passed."
