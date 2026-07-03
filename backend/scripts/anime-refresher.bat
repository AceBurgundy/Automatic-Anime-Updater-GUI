@echo off
setlocal
cd /d "%~dp0\.."
call .venv\Scripts\python.exe main.py --start-automation --synchronize-posters %*
endlocal
