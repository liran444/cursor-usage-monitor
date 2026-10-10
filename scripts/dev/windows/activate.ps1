# Activate the dev venv.
# Dot-source to keep it in your current terminal:
#   . .\scripts\dev\windows\activate.ps1
param(
    [switch]$NoShell
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$Activate = Join-Path $Root ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $Activate)) {
    Write-Error "No .venv found. Run .\scripts\dev\windows\install.ps1 first."
}

Set-Location $Root
. $Activate

if ($NoShell -or $MyInvocation.InvocationName -eq '.') {
    Write-Host "Dev environment active in this shell."
    return
}

Write-Host "To activate in THIS terminal instead, run:"
Write-Host "  . .\scripts\dev\windows\activate.ps1"
Write-Host ""
Write-Host "Opening a new dev shell..."
$shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }
& $shell -NoExit -Command "Set-Location '$Root'; . '$Activate'; Write-Host 'Dev shell ready. Try: cursor-usage tray | pytest'"
