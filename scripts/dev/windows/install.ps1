# Developer setup: editable install in .venv (Windows)
#Requires -Version 5.1
param(
    [switch]$NoShell
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Set-Location $Root

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
        [System.Environment]::GetEnvironmentVariable("Path", "User")
}

Refresh-Path

function Get-PythonCandidatePath {
    param(
        [string]$Exe,
        [string[]]$Args
    )

    try {
        $command = Get-Command $Exe -ErrorAction Stop
        $path = $command.Source
        if ($path -match '\\WindowsApps\\') {
            return $null
        }
        return @{ Exe = $Exe; Args = $Args; Path = $path }
    } catch {
        return $null
    }
}

function Test-PythonCandidate {
    param($Candidate)

    $output = & $Candidate.Exe @($Candidate.Args + @(
        "-c",
        "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    )) 2>&1
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    $versionText = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($versionText)) {
        return $null
    }

    try {
        $version = [version]$versionText
    } catch {
        return $null
    }

    if ($version -lt [version]"3.10") {
        return $null
    }

    return @{
        Candidate = $Candidate
        Version = $versionText
    }
}

function Get-KnownPythonCandidates {
    $candidates = @()

    $launcher = Join-Path $env:LOCALAPPDATA "Programs\Python\Launcher\py.exe"
    if (Test-Path $launcher) {
        $candidates += @{ Exe = $launcher; Args = @("-3"); Path = $launcher }
    }

    $pythonRoot = Join-Path $env:LOCALAPPDATA "Programs\Python"
    if (Test-Path $pythonRoot) {
        Get-ChildItem -Path (Join-Path $pythonRoot "Python*\python.exe") -ErrorAction SilentlyContinue |
            Sort-Object { $_.FullName } -Descending |
            ForEach-Object {
                $candidates += @{ Exe = $_.FullName; Args = @(); Path = $_.FullName }
            }
    }

    return $candidates
}

function Find-Python {
    $candidates = @()

    $py = Get-PythonCandidatePath -Exe "py" -Args @("-3")
    if ($py) { $candidates += $py }

    foreach ($name in @("python", "python3")) {
        $candidate = Get-PythonCandidatePath -Exe $name -Args @()
        if ($candidate) { $candidates += $candidate }
    }

    $candidates += Get-KnownPythonCandidates

    $seen = @{}
    foreach ($candidate in $candidates) {
        $key = "$($candidate.Exe)|$($candidate.Args -join ',')"
        if ($seen.ContainsKey($key)) {
            continue
        }
        $seen[$key] = $true

        $result = Test-PythonCandidate -Candidate $candidate
        if ($result) {
            return $result
        }
    }

    return $null
}

function Show-ManualPythonInstructions {
    Write-Host ""
    Write-Host "Install Python 3.10+ from https://www.python.org/downloads/"
    Write-Host "During setup, check 'Add python.exe to PATH'."
    Write-Host "Also disable Windows Store aliases:"
    Write-Host "  Settings -> Apps -> Advanced app settings -> App execution aliases"
    Write-Host "  Turn off python.exe and python3.exe"
    Write-Host ""
    Write-Host "Open a new terminal, then re-run:"
    Write-Host "  .\scripts\dev\windows\install.ps1"
}

function Test-WingetInstallSucceeded {
    param(
        [int]$ExitCode,
        [string]$Output
    )

    if ($ExitCode -eq 0) {
        return $true
    }

    return $Output -match 'already installed|No available upgrade found|No newer package versions are available'
}

function Try-InstallPythonWithWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        return $false
    }

    $response = Read-Host "Install Python 3.12 with winget? [Y/n]"
    if ($response -match '^(n|no)$') {
        return $false
    }

    Write-Host "Installing Python 3.12 with winget..."
    $wingetOutput = winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements 2>&1 | Out-String
    if (-not (Test-WingetInstallSucceeded -ExitCode $LASTEXITCODE -Output $wingetOutput)) {
        Write-Host $wingetOutput
        Write-Error "winget install failed. Install Python manually and re-run this script."
    }

    if ($wingetOutput -match 'already installed|No available upgrade found') {
        Write-Host "Python 3.12 is already installed."
    } else {
        Write-Host "Python 3.12 installed."
    }

    Refresh-Path
    return $true
}

$python = Find-Python
if (-not $python) {
    Write-Host "Python 3.10+ not found."
    if (-not (Try-InstallPythonWithWinget)) {
        Show-ManualPythonInstructions
        exit 1
    }

    $python = Find-Python
    if (-not $python) {
        Write-Host ""
        Write-Host "Python was installed but is not available in this shell yet."
        Show-ManualPythonInstructions
        exit 1
    }
}

Write-Host "Using Python $($python.Version) ($($python.Candidate.Path))"
Write-Host "Creating .venv in $Root"

& $python.Candidate.Exe @($python.Candidate.Args + @("-m", "venv", ".venv"))

$Activate = Join-Path $Root ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $Activate)) {
    Write-Error "Failed to create .venv. Re-run after installing Python with the venv module enabled."
}

. $Activate

function Remove-CorruptedPipPackages {
    $sitePackages = Join-Path $Root ".venv\Lib\site-packages"
    if (-not (Test-Path $sitePackages)) {
        return
    }
    Get-ChildItem -Path $sitePackages -Directory -Filter "~*" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-CorruptedPipPackages

python -m pip install -U pip
pip install -e ".[dev]"

$CursorUsage = Join-Path $Root ".venv\Scripts\cursor-usage.exe"
if (-not (Test-Path $CursorUsage)) {
    Write-Error "Install finished but cursor-usage.exe is missing. Re-run this script."
}
& $CursorUsage --help | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Repairing broken editable install..."
    Remove-CorruptedPipPackages
    pip install --force-reinstall -e ".[dev]"
    & $CursorUsage --help | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "cursor-usage entry point is broken. Try: Remove-Item -Recurse -Force .venv, then re-run install."
    }
}

Write-Host ""
Write-Host "Done. Dev environment installed."
Write-Host ""
Write-Host "Activate with:"
Write-Host "  . .\scripts\dev\windows\activate.ps1"
Write-Host ""
Write-Host "Then run: cursor-usage tray"
Write-Host "Verify:   .\scripts\dev\windows\verify.ps1"

if (-not $NoShell) {
    Write-Host ""
    Write-Host "Tip: use -NoShell to skip this message in automation."
}
