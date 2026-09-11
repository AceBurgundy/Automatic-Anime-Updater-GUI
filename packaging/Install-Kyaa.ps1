# ==============================================================================
# Kyaa!! Standalone GUI Installation Wizard
# ==============================================================================

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ReleaseDir = Join-Path (Split-Path -Parent $ScriptDir) "build\windows\x64\runner\Release"
if (-not (Test-Path $ReleaseDir)) {
    $ReleaseDir = Join-Path $ScriptDir "app"
}

$DefaultInstallDir = Join-Path $env:LOCALAPPDATA "Programs\KyaaApp"

# ------------------------------------------------------------------------------
# Create Main Form
# ------------------------------------------------------------------------------
$form = New-Object System.Windows.Forms.Form
$form.Text = "Kyaa!! Setup"
$form.Size = New-Object System.Drawing.Size(580, 480)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(20, 18, 24) # AMOLED Dark
$form.ForeColor = [System.Drawing.Color]::FromArgb(230, 224, 233)
$form.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)

# Header Banner
$headerPanel = New-Object System.Windows.Forms.Panel
$headerPanel.Size = New-Object System.Drawing.Size(580, 75)
$headerPanel.Location = New-Object System.Drawing.Point(0, 0)
$headerPanel.BackColor = [System.Drawing.Color]::FromArgb(33, 31, 38)
$form.Controls.Add($headerPanel)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "Kyaa!!"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)
$titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(208, 188, 255) # Purple Iris
$titleLabel.Location = New-Object System.Drawing.Point(24, 14)
$titleLabel.AutoSize = $true
$headerPanel.Controls.Add($titleLabel)

$subtitleLabel = New-Object System.Windows.Forms.Label
$subtitleLabel.Text = "Automated Anime Episode & Poster Sync Engine"
$subtitleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$subtitleLabel.ForeColor = [System.Drawing.Color]::FromArgb(202, 196, 208)
$subtitleLabel.Location = New-Object System.Drawing.Point(26, 44)
$subtitleLabel.AutoSize = $true
$headerPanel.Controls.Add($subtitleLabel)

# Destination Directory Group
$dirLabel = New-Object System.Windows.Forms.Label
$dirLabel.Text = "Installation Directory:"
$dirLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$dirLabel.Location = New-Object System.Drawing.Point(28, 95)
$dirLabel.AutoSize = $true
$form.Controls.Add($dirLabel)

$dirBox = New-Object System.Windows.Forms.TextBox
$dirBox.Text = $DefaultInstallDir
$dirBox.Location = New-Object System.Drawing.Point(28, 125)
$dirBox.Size = New-Object System.Drawing.Size(400, 28)
$dirBox.BackColor = [System.Drawing.Color]::FromArgb(40, 36, 46)
$dirBox.ForeColor = [System.Drawing.Color]::White
$dirBox.BorderStyle = "FixedSingle"
$form.Controls.Add($dirBox)

$browseBtn = New-Object System.Windows.Forms.Button
$browseBtn.Text = "Browse..."
$browseBtn.Location = New-Object System.Drawing.Point(440, 123)
$browseBtn.Size = New-Object System.Drawing.Size(100, 30)
$browseBtn.FlatStyle = "Flat"
$browseBtn.BackColor = [System.Drawing.Color]::FromArgb(55, 48, 66)
$browseBtn.ForeColor = [System.Drawing.Color]::FromArgb(208, 188, 255)
$browseBtn.FlatAppearance.BorderSize = 0
$browseBtn.Cursor = [System.Windows.Forms.Cursors]::Hand
$browseBtn.Add_Click({
    $fbd = New-Object System.Windows.Forms.FolderBrowserDialog
    $fbd.SelectedPath = $dirBox.Text
    if ($fbd.ShowDialog() -eq "OK") {
        $dirBox.Text = $fbd.SelectedPath
    }
})
$form.Controls.Add($browseBtn)

# Options Group
$optionsLabel = New-Object System.Windows.Forms.Label
$optionsLabel.Text = "Installation Options:"
$optionsLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$optionsLabel.Location = New-Object System.Drawing.Point(28, 175)
$optionsLabel.AutoSize = $true
$form.Controls.Add($optionsLabel)

$chkDesktop = New-Object System.Windows.Forms.CheckBox
$chkDesktop.Text = "Create Desktop Shortcut"
$chkDesktop.Checked = $true
$chkDesktop.Location = New-Object System.Drawing.Point(32, 205)
$chkDesktop.Size = New-Object System.Drawing.Size(300, 24)
$form.Controls.Add($chkDesktop)

$chkStartMenu = New-Object System.Windows.Forms.CheckBox
$chkStartMenu.Text = "Create Start Menu Shortcut"
$chkStartMenu.Checked = $true
$chkStartMenu.Location = New-Object System.Drawing.Point(32, 235)
$chkStartMenu.Size = New-Object System.Drawing.Size(300, 24)
$form.Controls.Add($chkStartMenu)

$chkLaunch = New-Object System.Windows.Forms.CheckBox
$chkLaunch.Text = "Launch Kyaa!! after installation completes"
$chkLaunch.Checked = $true
$chkLaunch.Location = New-Object System.Drawing.Point(32, 265)
$chkLaunch.Size = New-Object System.Drawing.Size(350, 24)
$form.Controls.Add($chkLaunch)

# Progress Bar & Status
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "Ready to install."
$statusLabel.Location = New-Object System.Drawing.Point(28, 310)
$statusLabel.Size = New-Object System.Drawing.Size(510, 20)
$statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(202, 196, 208)
$form.Controls.Add($statusLabel)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(28, 335)
$progressBar.Size = New-Object System.Drawing.Size(512, 18)
$progressBar.Style = "Blocks"
$form.Controls.Add($progressBar)

# Footer Buttons
$cancelBtn = New-Object System.Windows.Forms.Button
$cancelBtn.Text = "Cancel"
$cancelBtn.Location = New-Object System.Drawing.Point(330, 385)
$cancelBtn.Size = New-Object System.Drawing.Size(95, 36)
$cancelBtn.FlatStyle = "Flat"
$cancelBtn.BackColor = [System.Drawing.Color]::FromArgb(55, 48, 66)
$cancelBtn.ForeColor = [System.Drawing.Color]::White
$cancelBtn.FlatAppearance.BorderSize = 0
$cancelBtn.Cursor = [System.Windows.Forms.Cursors]::Hand
$cancelBtn.Add_Click({ $form.Close() })
$form.Controls.Add($cancelBtn)

$installBtn = New-Object System.Windows.Forms.Button
$installBtn.Text = "Install"
$installBtn.Location = New-Object System.Drawing.Point(440, 385)
$installBtn.Size = New-Object System.Drawing.Size(100, 36)
$installBtn.FlatStyle = "Flat"
$installBtn.BackColor = [System.Drawing.Color]::FromArgb(79, 55, 139) # Primary Container
$installBtn.ForeColor = [System.Drawing.Color]::FromArgb(208, 188, 255)
$installBtn.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
$installBtn.FlatAppearance.BorderSize = 0
$installBtn.Cursor = [System.Windows.Forms.Cursors]::Hand

$installBtn.Add_Click({
    $targetDir = $dirBox.Text.Trim()
    if ([string]::IsNullOrEmpty($targetDir)) {
        [System.Windows.Forms.MessageBox]::Show("Please specify a valid destination folder.", "Invalid Path", "OK", "Warning")
        return
    }

    $installBtn.Enabled = $false
    $cancelBtn.Enabled = $false
    $browseBtn.Enabled = $false
    $dirBox.Enabled = $false
    $chkDesktop.Enabled = $false
    $chkStartMenu.Enabled = $false
    $chkLaunch.Enabled = $false

    $statusLabel.Text = "Preparing installation directory..."
    $progressBar.Value = 10
    $form.Refresh()

    try {
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        }

        # Copy release files
        $statusLabel.Text = "Copying application binaries and assets..."
        $progressBar.Value = 30
        $form.Refresh()

        if (Test-Path $ReleaseDir) {
            Copy-Item -Path "$ReleaseDir\*" -Destination $targetDir -Recurse -Force
        } else {
            throw "Release binary directory not found at $ReleaseDir"
        }

        $progressBar.Value = 70
        $statusLabel.Text = "Configuring shortcuts and uninstaller..."
        $form.Refresh()

        $exePath = Join-Path $targetDir "kyaa_app.exe"
        $wsh = New-Object -ComObject WScript.Shell

        # Desktop Shortcut
        if ($chkDesktop.Checked) {
            $desktopPath = [System.Environment]::GetFolderPath("Desktop")
            $shortcut = $wsh.CreateShortcut((Join-Path $desktopPath "Kyaa!!.lnk"))
            $shortcut.TargetPath = $exePath
            $shortcut.WorkingDirectory = $targetDir
            $shortcut.Description = "Kyaa!! Anime Refresher GUI"
            $shortcut.Save()
        }

        # Start Menu Shortcut
        if ($chkStartMenu.Checked) {
            $startMenuDir = Join-Path ([System.Environment]::GetFolderPath("Programs")) "Kyaa!!"
            if (-not (Test-Path $startMenuDir)) {
                New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null
            }
            $shortcut = $wsh.CreateShortcut((Join-Path $startMenuDir "Kyaa!!.lnk"))
            $shortcut.TargetPath = $exePath
            $shortcut.WorkingDirectory = $targetDir
            $shortcut.Description = "Kyaa!! Anime Refresher GUI"
            $shortcut.Save()
        }

        # Generate Uninstaller
        $uninstallScript = @"
@echo off
taskkill /F /IM kyaa_app.exe 2>nul
timeout /t 1 >nul
rmdir /S /Q "$targetDir" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Kyaa!!\*.lnk" 2>nul
rmdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Kyaa!!" 2>nul
del "%USERPROFILE%\Desktop\Kyaa!!.lnk" 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\KyaaApp" /f 2>nul
echo Kyaa!! has been successfully uninstalled.
pause
"@
        Set-Content -Path (Join-Path $targetDir "Uninstall.bat") -Value $uninstallScript

        # Register in Windows Add/Remove Programs
        $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\KyaaApp"
        if (-not (Test-Path $regPath)) {
            New-Item -Path $regPath -Force | Out-Null
        }
        Set-ItemProperty -Path $regPath -Name "DisplayName" -Value "Kyaa!! Anime Refresher"
        Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value "1.0.0"
        Set-ItemProperty -Path $regPath -Name "Publisher" -Value "Anime Refresher Team"
        Set-ItemProperty -Path $regPath -Name "InstallLocation" -Value $targetDir
        Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "`"$targetDir\Uninstall.bat`""
        Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value "$exePath,0"

        $progressBar.Value = 100
        $statusLabel.Text = "Installation completed successfully!"
        $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(115, 218, 164) # Emerald Mint
        $form.Refresh()

        [System.Windows.Forms.MessageBox]::Show("Kyaa!! has been successfully installed to:`n$targetDir", "Setup Complete", "OK", "Information")

        if ($chkLaunch.Checked -and (Test-Path $exePath)) {
            Start-Process -FilePath $exePath -WorkingDirectory $targetDir
        }

        $form.Close()
    } catch {
        [System.Windows.Forms.MessageBox]::Show("Installation failed:`n$_", "Installation Error", "OK", "Error")
        $statusLabel.Text = "Installation failed."
        $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(255, 180, 171)
        $installBtn.Enabled = $true
        $cancelBtn.Enabled = $true
    }
})

$form.Controls.Add($installBtn)

# Show Dialog
[void]$form.ShowDialog()
