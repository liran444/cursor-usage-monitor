# Download VC++ 2015-2022 x64 redistributable for bundling in Inno Setup.
$ErrorActionPreference = "Stop"
$Dir = Join-Path $PSScriptRoot "redist"
$Out = Join-Path $Dir "vc_redist.x64.exe"
$Url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"

if (-not (Test-Path $Dir)) {
    New-Item -ItemType Directory -Path $Dir | Out-Null
}
if (Test-Path $Out) {
    Write-Host "VC++ redist already present: $Out"
    exit 0
}
Write-Host "Downloading VC++ redist..."
Invoke-WebRequest -Uri $Url -OutFile $Out -UseBasicParsing
Write-Host "Saved: $Out"
