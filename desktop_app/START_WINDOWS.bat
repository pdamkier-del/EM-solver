@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "EM1_PY=%LOCALAPPDATA%\EM1\desktop-python313-20261105\Scripts\python.exe"
if not exist "%EM1_PY%" (
 echo Run INSTALL_WINDOWS.bat once before the exam.
 pause
 exit /b 1
)
"%EM1_PY%" -c "import sys,struct,sysconfig; assert sys.version_info[:2] == (3,13) and struct.calcsize('P') == 8 and sysconfig.get_platform() == 'win-amd64' and not sysconfig.get_config_var('Py_GIL_DISABLED')" >nul 2>&1
if errorlevel 1 (
 echo This package requires standard CPython 3.13 x64. Run INSTALL_WINDOWS.bat.
 pause
 exit /b 1
)
set "EM1_BACKEND_PYTHON=%EM1_PY%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
"%EM1_PY%" "%~dp0run_app.py" > "%~dp0EM1_START_LOG.txt" 2>&1
if errorlevel 1 (
 type "%~dp0EM1_START_LOG.txt"
 pause
 exit /b 1
)
