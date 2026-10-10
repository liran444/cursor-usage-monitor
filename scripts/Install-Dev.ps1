# Developer setup: editable install in .venv (Windows)
#Requires -Version 5.1
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

$venvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Failed to create .venv. Re-run after installing Python with the venv module enabled."
}

& $venvPython -m pip install -U pip
& $venvPython -m pip install -e ".[dev]"

Write-Host ""
Write-Host "Done. Activate and run:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  cursor-usage tray"
Write-Host ""
Write-Host "Tests: pytest"
