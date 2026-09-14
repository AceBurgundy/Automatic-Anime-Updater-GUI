@echo off
setlocal
cd /d "%~dp0\.."
if exist env\Scripts\python.exe (
    call env\Scripts\python.exe main.py --start-automation-stream %*
) else (
    call .venv\Scripts\python.exe main.py --start-automation-stream %*
)
endlocal
