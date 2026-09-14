@echo off
echo Starting local documentation server at http://localhost:9241 ...
start http://localhost:9241
python -m http.server 9241
