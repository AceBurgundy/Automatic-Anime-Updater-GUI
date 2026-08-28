# ==============================================================================
# Kyaa!! Standalone Distribution & Installer Packaging Script
# ==============================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$DistDir = Join-Path $ProjectDir "dist"
$ReleaseDir = Join-Path $ProjectDir "build\windows\x64\runner\Release"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "         BUILDING KYAA!! STANDALONE INSTALLER PACKAGE       " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Ensure Flutter Windows Release build exists
if (-not (Test-Path "$ReleaseDir\kyaa_app.exe")) {
    Write-Host "[1/3] Building Flutter Windows release binaries..." -ForegroundColor Yellow
    Push-Location $ProjectDir
    flutter build windows --release
    Pop-Location
} else {
    Write-Host "[1/3] Verified existing Flutter Windows release binary." -ForegroundColor Green
}

# Step 2: Prepare Dist Directory
Write-Host "[2/3] Preparing output distribution directory..." -ForegroundColor Yellow
if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
}

$PackageDir = Join-Path $DistDir "KyaaApp_v1.0.0_Standalone"
if (Test-Path $PackageDir) {
    Remove-Item -Recurse -Force $PackageDir
}
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null
$AppDir = Join-Path $PackageDir "app"
New-Item -ItemType Directory -Force -Path $AppDir | Out-Null

# Copy Release Binaries
Copy-Item -Path "$ReleaseDir\*" -Destination $AppDir -Recurse -Force

# Bundle Backend CLI Engine
$BackendSrc = Join-Path $ProjectDir "backend"
if (Test-Path $BackendSrc) {
    Write-Host "  -> Bundling backend engine into distribution..." -ForegroundColor Gray
    $BackendDest = Join-Path $AppDir "backend"
    if (-not (Test-Path $BackendDest)) {
        New-Item -ItemType Directory -Force -Path $BackendDest | Out-Null
    }
    # Use Robocopy to safely exclude locks, git directories, and caches
    robocopy "$BackendSrc" "$BackendDest" /E /XD __pycache__ .git debug_screenshots /XF *.db-shm *.db-wal *.pyc *.log /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "Robocopy failed to bundle backend with exit code $LASTEXITCODE"
    }
}

# Copy Installer Files
Copy-Item -Path (Join-Path $ScriptDir "Install-Kyaa.ps1") -Destination $PackageDir -Force

# Create Double-Click Setup.bat Launcher
$setupLauncher = @"
@echo off
title Launching Kyaa!! Setup...
powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File "%~dp0Install-Kyaa.ps1"
"@
Set-Content -Path (Join-Path $PackageDir "Setup.bat") -Value $setupLauncher

# Step 3: Create Zip Distribution Archive
Write-Host "[3/3] Generating portable installer package archive..." -ForegroundColor Yellow
$ZipOutput = Join-Path $DistDir "KyaaApp_v1.0.0_Windows_Setup.zip"
if (Test-Path $ZipOutput) {
    Remove-Item -Force $ZipOutput
}
Compress-Archive -Path "$PackageDir\*" -DestinationPath $ZipOutput -CompressionLevel Optimal

Write-Host "============================================================" -ForegroundColor Green
Write-Host "Packaging Complete!" -ForegroundColor Green
Write-Host "Installer Location: $PackageDir\Setup.bat" -ForegroundColor White
Write-Host "Archive Location:   $ZipOutput" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
