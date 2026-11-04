@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto nopy

set "PY_SPEC="

py -3.13 --version >nul 2>nul
if not errorlevel 1 set "PY_SPEC=-3.13"

if not defined PY_SPEC (
  py -3.12 --version >nul 2>nul
  if not errorlevel 1 set "PY_SPEC=-3.12"
)

if not defined PY_SPEC (
  py -3 --version >nul 2>nul
  if not errorlevel 1 set "PY_SPEC=-3"
)

if not defined PY_SPEC goto nopy

echo Bruger Python %PY_SPEC%
if exist .venv rmdir /s /q .venv
py %PY_SPEC% -m venv .venv
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

echo.
echo Klar. Dobbeltklik paa START_EM1_SOLVER.bat.
pause
exit /b 0

:nopy
echo Ingen egnet Python-installation blev fundet via Python Launcher.
echo Installer Python 3.13 eller 3.12 inklusive Python Launcher, og proev igen.
pause
exit /b 1

:failed
echo Installation fejlede. Laes fejlen ovenfor. Appen er ikke klar endnu.
pause
exit /b 1
