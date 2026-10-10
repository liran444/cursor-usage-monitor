# Developer setup: editable install in .venv (Windows)
#Requires -Version 5.1
param(
    [switch]$NoShell
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Find-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ Exe = "py"; Args = @("-3") }
    }
    foreach ($name in @("python", "python3")) {
        if (Get-Command $name -ErrorAction SilentlyContinue) {
            return @{ Exe = $name; Args = @() }
        }
    }
    return $null
}

$python = Find-PythonCommand
if (-not $python) {
    Write-Error @"
Python 3.10+ not found.

Install from https://www.python.org/downloads/
During setup, check "Add python.exe to PATH", then open a new terminal and re-run:

  .\scripts\Install-Dev.ps1
"@
}

$versionOutput = & $python.Exe @($python.Args + @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"))
$version = [version]$versionOutput
if ($version -lt [version]"3.10") {
    Write-Error "Python 3.10+ required (found $versionOutput)."
}

Write-Host "Using Python $versionOutput"
Write-Host "Creating .venv in $Root"

& $python.Exe @($python.Args + @("-m", "venv", ".venv"))

$Activate = Join-Path $Root ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $Activate)) {
    Write-Error "Failed to create .venv. Re-run after installing Python with the venv module enabled."
}

. $Activate

python -m pip install -U pip
pip install -e ".[dev]"

Write-Host ""
Write-Host "Done. Dev environment installed."

if ($NoShell) {
    Write-Host "Activate later with:"
    Write-Host "  . .\scripts\enter-dev.ps1"
    Write-Host ""
    Write-Host "Then run: cursor-usage tray"
    exit 0
}

Write-Host "Opening dev shell with venv active..."
& (Join-Path $PSScriptRoot "enter-dev.ps1")
