@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title CONTROLE MESTRE - Diagnostico
set "CM_PY="
py -3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if not errorlevel 1 set "CM_PY=py -3"
if not defined CM_PY (
  python -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
  if not errorlevel 1 set "CM_PY=python"
)
if not defined CM_PY (
  echo ERRO: Python 3.11+ nao encontrado.
  pause
  exit /b 1
)
%CM_PY% -u launch.py --diagnostico
set "CM_RC=%ERRORLEVEL%"
echo.
pause
exit /b %CM_RC%