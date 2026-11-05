@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=%LOCALAPPDATA%\EM1\desktop-python313-20261105\Scripts\python.exe"
if not exist "%PYTHON%" (
 echo Backend er ikke installeret. Koer INSTALL_WINDOWS.bat
 pause
 exit /b 1
)
"%PYTHON%" "%~dp0TEST_FYSIKMOTOR.py"
echo.
pause
