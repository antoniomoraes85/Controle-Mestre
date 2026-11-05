@echo off
cd /d "%~dp0"
echo CONTROLE MESTRE - Painel Web Premium v0.3
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 web_server.py
) else (
  python web_server.py
)
pause