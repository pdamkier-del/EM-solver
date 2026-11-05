@echo off
setlocal EnableExtensions
cd /d "%~dp0"
py -3.13 -c "import sys,struct,sysconfig; assert sys.version_info[:2] == (3,13) and struct.calcsize('P') == 8 and sysconfig.get_platform() == 'win-amd64' and not sysconfig.get_config_var('Py_GIL_DISABLED')" >nul 2>&1
if errorlevel 1 (
 echo Install standard CPython 3.13 x64 with the py launcher first.
 pause
 exit /b 1
)
py -3.13 -m pip download --only-binary=:all: --dest "%~dp0wheelhouse" -r "%~dp0requirements-windows-lock.txt"
if errorlevel 1 (
 echo Download failed. Offline preparation is incomplete.
 pause
 exit /b 1
)
echo Wheels ready. Run INSTALL_WINDOWS.bat, then test START_WINDOWS.bat with Wi-Fi off.
pause
