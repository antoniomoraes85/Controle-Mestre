@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUNBUFFERED=1"
title CONTROLE MESTRE - Painel Web Local

echo ============================================
echo  CONTROLE MESTRE - Inicializacao segura
echo ============================================
echo.

set "CM_PY="
py -3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if not errorlevel 1 set "CM_PY=py -3"
if not defined CM_PY (
  python -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
  if not errorlevel 1 set "CM_PY=python"
)
if not defined CM_PY (
  echo ERRO: nao encontrei Python 3.11 ou superior neste Windows.
  echo Instale Python 3.11+ e habilite o comando Python no PATH.
  echo Confira: https://www.python.org/downloads/windows/
  echo.
  pause
  exit /b 1
)

echo Interpretador: %CM_PY%
echo.
%CM_PY% -u launch.py
set "CM_RC=%ERRORLEVEL%"
echo.
if not "%CM_RC%"=="0" (
  echo A plataforma nao iniciou. Confira a mensagem acima.
  echo Para diagnosticar, execute diagnosticar_windows.bat.
) else (
  echo CONTROLE MESTRE encerrado.
)
echo.
pause
exit /b %CM_RC%