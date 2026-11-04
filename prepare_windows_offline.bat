@echo off
setlocal
cd /d "%~dp0"
echo Koer dette paa en Windows-computer med internet og Python 3.12 foer eksamen.
py -3.12 -m pip download --only-binary=:all: -r requirements-lock.txt -d wheelhouse
if errorlevel 1 (
  echo Download fejlede. Der er ikke en komplet offline-pakke endnu.
  pause
  exit /b 1
)
echo Kopier hele projektmappen inklusive wheelhouse til en tilsvarende Windows-computer.
echo Python 3.12 skal allerede vaere installeret paa maalcomputeren.
pause
exit /b 0
