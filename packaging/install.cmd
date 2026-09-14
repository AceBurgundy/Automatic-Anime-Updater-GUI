@echo off
setlocal
:: ==============================================================================
:: Kyaa!! Anime Refresher - Windows CMD Remote Web Bootstrapper Installer
:: Target Execution: curl -fsSL https://raw.githubusercontent.com/AceBurgundy/kyaa_anime_refresher/main/packaging/install.cmd -o install.cmd && install.cmd && del install.cmd
:: ==============================================================================

echo [Kyaa!! Setup] Initiating remote web installation via PowerShell...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/AceBurgundy/kyaa_anime_refresher/main/packaging/install.ps1 | iex"
endlocal
