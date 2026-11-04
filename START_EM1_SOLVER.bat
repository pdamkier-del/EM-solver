@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Det lokale miljoe mangler. Dobbeltklik foerst paa install_windows.bat.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" launch_em1.py
if errorlevel 1 (
  echo EM1 Solver kunne ikke starte. Laes fejlen ovenfor.
  pause
  exit /b 1
)
exit /b 0
