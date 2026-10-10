# Install Cursor Usage Monitor from extracted release folder
param(
    [string]$BundlePath = "$PSScriptRoot\..\..\..\dist\CursorUsageMonitor"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $BundlePath)) {
    Write-Error "Bundle not found: $BundlePath. Build first — see docs/BUILD.md"
}
$InstallDir = Join-Path $env:LOCALAPPDATA "CursorUsageMonitor"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path (Join-Path $BundlePath "*") -Destination $InstallDir -Recurse -Force
$Exe = Join-Path $InstallDir "cursor-usage.exe"
$Startup = [Environment]::GetFolderPath("Startup")
$Shortcut = Join-Path $Startup "Cursor Usage Monitor.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Link = $WshShell.CreateShortcut($Shortcut)
$Link.TargetPath = $Exe
$Link.Arguments = "tray"
$Link.WorkingDirectory = $InstallDir
$Link.Save()
Write-Host "Installed to $InstallDir and Startup shortcut."
