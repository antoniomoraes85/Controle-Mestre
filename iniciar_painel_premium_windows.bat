@echo off
cd /d "%~dp0"
echo CONTROLE MESTRE - Painel Web Premium v0.3
where py >nul 2>&1
if %errorlevel%==0 (
  start "" "http://127.0.0.1:8765"
  py -3 web_server.py
) else (
  start "" "http://127.0.0.1:8765"
  python web_server.py
)
pause