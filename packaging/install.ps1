# ==============================================================================
# Kyaa!! Anime Refresher - Remote Web Bootstrapper Installer
# Target Execution: irm https://raw.githubusercontent.com/AceBurgundy/kyaa_anime_refresher/main/packaging/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Purple
Write-Host "                KYAA!! ANIME REFRESHER - WEB INSTALLER                      " -ForegroundColor Magenta
Write-Host "============================================================================" -ForegroundColor Purple
Write-Host ""

$RepoOwner = "AceBurgundy"
$RepoName = "kyaa_anime_refresher"
$Branch = "main"

$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\KyaaAnimeRefresher"
$ZipUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/heads/$Branch.zip"
$TempZip = Join-Path $env:TEMP "KyaaInstaller_$([Guid]::NewGuid().ToString().Substring(0,8)).zip"
$TempExtract = Join-Path $env:TEMP "KyaaExtract_$([Guid]::NewGuid().ToString().Substring(0,8))"

try {
    # 1. Check Python Availability
    Write-Host "[1/5] Checking environment prerequisites..." -ForegroundColor Cyan
    $PythonBin = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path
    if (-not $PythonBin) {
        Write-Host "[!] Warning: python.exe was not found in PATH." -ForegroundColor Yellow
        Write-Host "    Python 3.10+ is required to run the automation engine." -ForegroundColor Yellow
        Write-Host "    Download Python from https://www.python.org/downloads/ if needed." -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Detected Python: $PythonBin" -ForegroundColor Green
    }

    # 2. Download Release Archive
    Write-Host ""
    Write-Host "[2/5] Downloading latest repository payload from GitHub..." -ForegroundColor Cyan
    Write-Host "      Source: $ZipUrl" -ForegroundColor Gray
    
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZip -UseBasicParsing
    Write-Host "[OK] Download completed ($([Math]::Round((Get-Item $TempZip).Length / 1MB, 2)) MB)" -ForegroundColor Green

    # 3. Extract & Deploy Files
    Write-Host ""
    Write-Host "[3/5] Extracting application payload to $InstallDir..." -ForegroundColor Cyan
    if (Test-Path $TempExtract) { Remove-Item -Path $TempExtract -Recurse -Force | Out-Null }
    Expand-Archive -Path $TempZip -DestinationPath $TempExtract -Force
    
    $SubFolder = Join-Path $TempExtract "$RepoName-$Branch"
    if (-not (Test-Path $SubFolder)) {
        $SubFolder = Get-ChildItem -Path $TempExtract | Where-Object { $_.PSIsContainer } | Select-Object -First 1 -ExpandProperty FullName
    }

    if (Test-Path $InstallDir) {
        Remove-Item -Path "$InstallDir\*" -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
    } else {
        New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    }

    Copy-Item -Path "$SubFolder\*" -Destination $InstallDir -Recurse -Force
    Write-Host "[OK] Payload deployed successfully." -ForegroundColor Green

    # 4. Configure Python Backend Virtual Environment
    Write-Host ""
    Write-Host "[4/5] Initializing Python backend environment..." -ForegroundColor Cyan
    $BackendDir = Join-Path $InstallDir "backend"
    if (Test-Path $BackendDir) {
        $VenvDir = Join-Path $BackendDir "env"
        if ($PythonBin) {
            Write-Host "      Creating virtual environment at $VenvDir..." -ForegroundColor Gray
            Start-Process -FilePath $PythonBin -ArgumentList "-m venv `"$VenvDir`"" -Wait -NoNewWindow
            
            $VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
            $ReqFile = Join-Path $BackendDir "requirements.txt"
            if ((Test-Path $VenvPip) -and (Test-Path $ReqFile)) {
                Write-Host "      Installing backend Python dependencies..." -ForegroundColor Gray
                Start-Process -FilePath $VenvPip -ArgumentList "install -r `"$ReqFile`"" -Wait -NoNewWindow
            }
        }
    }

    # 5. Create Shortcuts & Register Uninstaller
    Write-Host ""
    Write-Host "[5/5] Creating Desktop & Start Menu shortcuts..." -ForegroundColor Cyan
    
    $Wsh = New-Object -ComObject WScript.Shell
    $ExePath = Join-Path $InstallDir "backend\env\Scripts\python.exe"
    $MainPy = Join-Path $InstallDir "backend\main.py"

    # Desktop Shortcut
    $DesktopPath = [System.Environment]::GetFolderPath("Desktop")
    $Shortcut = $Wsh.CreateShortcut((Join-Path $DesktopPath "Kyaa!! Anime Refresher.lnk"))
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-ExecutionPolicy Bypass -NoExit -Command `"cd /d '$BackendDir'; .\env\Scripts\python.exe main.py`""
    $Shortcut.WorkingDirectory = $BackendDir
    $Shortcut.Description = "Kyaa!! Anime Refresher Sync Engine"
    $Shortcut.Save()

    # Start Menu Shortcut
    $StartMenuDir = Join-Path ([System.Environment]::GetFolderPath("Programs")) "Kyaa!!"
    if (-not (Test-Path $StartMenuDir)) { New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null }
    $ShortcutSM = $Wsh.CreateShortcut((Join-Path $StartMenuDir "Kyaa!! Anime Refresher.lnk"))
    $ShortcutSM.TargetPath = "powershell.exe"
    $ShortcutSM.Arguments = "-ExecutionPolicy Bypass -NoExit -Command `"cd /d '$BackendDir'; .\env\Scripts\python.exe main.py`""
    $ShortcutSM.WorkingDirectory = $BackendDir
    $ShortcutSM.Description = "Kyaa!! Anime Refresher Sync Engine"
    $ShortcutSM.Save()

    # Generate Uninstaller
    $UninstallScript = @"
@echo off
echo Uninstalling Kyaa!! Anime Refresher...
rmdir /S /Q "$InstallDir" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Kyaa!!\*.lnk" 2>nul
rmdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Kyaa!!" 2>nul
del "%USERPROFILE%\Desktop\Kyaa!! Anime Refresher.lnk" 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\KyaaAnimeRefresher" /f 2>nul
echo [OK] Uninstalled successfully.
pause
"@
    Set-Content -Path (Join-Path $InstallDir "Uninstall.bat") -Value $UninstallScript

    # Register in Windows Add/Remove Programs
    $RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\KyaaAnimeRefresher"
    if (-not (Test-Path $RegPath)) { New-Item -Path $RegPath -Force | Out-Null }
    Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "Kyaa!! Anime Refresher"
    Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "1.1.0"
    Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "AceBurgundy"
    Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value $InstallDir
    Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value "`"$InstallDir\Uninstall.bat`""

    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host "        [✓] KYAA!! ANIME REFRESHER INSTALLED SUCCESSFULLY!                  " -ForegroundColor Green
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host " Installation Location : $InstallDir" -ForegroundColor White
    Write-Host " Desktop Shortcut     : Created" -ForegroundColor White
    Write-Host " Start Menu Shortcut  : Created" -ForegroundColor White
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "[!] Installation failed: $_" -ForegroundColor Red
}
finally {
    if (Test-Path $TempZip) { Remove-Item -Path $TempZip -Force -ErrorAction SilentlyContinue | Out-Null }
    if (Test-Path $TempExtract) { Remove-Item -Path $TempExtract -Recurse -Force -ErrorAction SilentlyContinue | Out-Null }
}
