@echo off
setlocal
cd /d "%~dp0\.."
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)
.venv\Scripts\python.exe -c "import PySide6.QtWidgets, esptool, serial" >nul 2>&1
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install -r desktop\requirements.txt
  if errorlevel 1 goto :error
)
.venv\Scripts\python.exe desktop\main.py %*
if errorlevel 1 goto :error
exit /b 0
:error
echo.
echo Start fehlgeschlagen. Benoetigt wird Python 3.10 oder neuer in 64 Bit.
pause
exit /b 1
