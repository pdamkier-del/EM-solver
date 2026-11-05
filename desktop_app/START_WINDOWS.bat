@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "EM1_PY=%LOCALAPPDATA%\EM1\desktop-development-20261105\Scripts\python.exe"
if not exist "%EM1_PY%" (
 echo Run INSTALL_WINDOWS.bat once before the exam.
 pause
 exit /b 1
)
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
"%EM1_PY%" "%~dp0run_app.py" > "%~dp0EM1_START_LOG.txt" 2>&1
if errorlevel 1 (
 type "%~dp0EM1_START_LOG.txt"
 pause
 exit /b 1
)
