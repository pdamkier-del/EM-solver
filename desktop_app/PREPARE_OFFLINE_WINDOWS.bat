@echo off
setlocal EnableExtensions
cd /d "%~dp0"
py -3.12 -m pip download --only-binary=:all: --dest "%~dp0wheelhouse" -r "%~dp0requirements-windows-lock.txt"
if errorlevel 1 (
 echo Download failed. Offline preparation is incomplete.
 pause
 exit /b 1
)
echo Wheels ready. Run INSTALL_WINDOWS.bat, then test START_WINDOWS.bat with Wi-Fi off.
pause
