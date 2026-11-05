@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=%LOCALAPPDATA%\EM1\backend312\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=%LOCALAPPDATA%\EM1\backend313\Scripts\python.exe"
if not exist "%PYTHON%" (
 echo Backend er ikke installeret. Koer SETUP_BACKEND_WINDOWS.bat
 pause
 exit /b 1
)
"%PYTHON%" "%~dp0TEST_FYSIKMOTOR.py"
echo.
pause
