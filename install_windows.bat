@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto nopy
py -3.12 -m venv .venv
if errorlevel 1 goto failed
if exist wheelhouse\*.whl (
  ".venv\Scripts\python.exe" -m pip install --no-index --find-links="%~dp0wheelhouse" -r requirements-lock.txt
) else (
  echo Installation kraever internet nu. Drift under eksamen er offline.
  ".venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
)
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto failed
".venv\Scripts\python.exe" launch_em1.py --check
if errorlevel 1 goto failed
echo Klar. Dobbeltklik paa START_EM1_SOLVER.bat.
pause
exit /b 0
:nopy
echo Installer Python 3.12 til Windows inklusive Python Launcher. Proev derefter igen.
pause
exit /b 1
:failed
echo Installation fejlede. Laes fejlen ovenfor. Appen er ikke klar endnu.
pause
exit /b 1
