@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Det lokale miljoe mangler. Dobbeltklik foerst paa install_windows.bat.
  pause
  exit /b 1
)
rem Start den lokale motor minimeret. Edge/Chrome aabnes som et separat app-vindue.
start "EM1 Solver Engine" /min ".venv\Scripts\python.exe" launch_em1.py
exit /b 0
