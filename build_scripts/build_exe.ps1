# Build Windows Executable (.exe) and Zip Package for OSB
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

Write-Host "=== Building OSB Windows Standalone Executable ===" -ForegroundColor Cyan
pyinstaller osb.spec --clean --noconfirm

$ExePath = Join-Path $RootDir "dist\OSB.exe"
if (-not (Test-Path $ExePath)) {
    Write-Error "OSB.exe was not generated at $ExePath"
    exit 1
}

Write-Host "=== Packaging Windows Zip Archive ===" -ForegroundColor Cyan
$ZipPath = Join-Path $RootDir "dist\OSB-windows-x64.zip"
if (Test-Path $ZipPath) {
    Remove-Item -Force $ZipPath
}

Compress-Archive -Path $ExePath -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host "=== Windows Build Complete ===" -ForegroundColor Green
Get-ChildItem -Path (Join-Path $RootDir "dist")
