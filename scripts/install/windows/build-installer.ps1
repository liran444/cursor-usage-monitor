# Build PyInstaller dist and compile Inno Setup installer to release/
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$Version = & $python (Join-Path $RepoRoot "scripts\build\read_version.py")
$ReleaseDir = Join-Path $RepoRoot "release"
$Iscc = $env:ISCC

if (-not $Iscc) {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $Iscc = $c; break }
    }
}
if (-not $Iscc -or -not (Test-Path $Iscc)) {
    Write-Error "Inno Setup ISCC.exe not found. Install Inno Setup 6 or set ISCC env var."
}

& (Join-Path $RepoRoot "scripts\install\windows\bundle-vcredist.ps1")
& (Join-Path $RepoRoot "scripts\build\build.ps1")

if (-not (Test-Path (Join-Path $RepoRoot "dist\cursor-usage"))) {
    Write-Error "dist\cursor-usage not found after build."
}

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
$OutBase = Join-Path $ReleaseDir "CursorUsageSetup-$Version-x64"

& $Iscc "/DAppVersion=$Version" "/DRepoRoot=$RepoRoot" (Join-Path $PSScriptRoot "cursor-usage.iss")
# Note: if RepoRoot contains spaces, Inno Setup 6 accepts /DRepoRoot="C:\path with spaces"

Write-Host "Installer: $OutBase.exe"
