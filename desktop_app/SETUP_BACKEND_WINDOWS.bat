@echo off
setlocal
cd /d "%~dp0"
set "LOG=%~dp0EM1_BACKEND_SETUP_LOG.txt"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0SETUP_BACKEND_WINDOWS.ps1" > "%LOG%" 2>&1
if errorlevel 1 (
 echo Backendinstallation fejlede. Se EM1_BACKEND_SETUP_LOG.txt.
 type "%LOG%"
 pause
 exit /b 1
)
type "%LOG%"
echo.
pause
