@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title EM1 Solver - Windows desktop
set "LOG=%~dp0EM1_START_LOG.txt"
set "VENV=%LOCALAPPDATA%\EM1\v"
set "VPY=%VENV%\Scripts\python.exe"
echo === EM1 Solver opstart %date% %time% === > "%LOG%"
echo Programmappe: %cd% >> "%LOG%"
echo Pythonmiljoe: %VENV% >> "%LOG%"
echo.
echo EM1 Solver starter ...
echo.
if not exist "app.py" (
  echo FEJL: app.py mangler. Udpak hele zip-filen.
  echo FEJL: app.py mangler >> "%LOG%"
  goto fail
)
set "PY_CMD="
where py >nul 2>&1
if not errorlevel 1 (
  for %%V in (3.13 3.12 3.11 3.10 3.14) do (
    if not defined PY_CMD (
      py -%%V -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
      if not errorlevel 1 set "PY_CMD=py -%%V"
    )
  )
)
if not defined PY_CMD (
  where python >nul 2>&1
  if not errorlevel 1 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo FEJL: Python findes ikke.
  echo FEJL: Python findes ikke >> "%LOG%"
  goto fail
)
echo Python: %PY_CMD% >> "%LOG%"
%PY_CMD% --version >> "%LOG%" 2>&1
if errorlevel 1 goto fail
if not exist "%VPY%" (
  echo Opretter kort lokalt Python-miljoe ...
  echo Opretter venv... >> "%LOG%"
  if not exist "%LOCALAPPDATA%\EM1" mkdir "%LOCALAPPDATA%\EM1" >> "%LOG%" 2>&1
  %PY_CMD% -m venv "%VENV%" >> "%LOG%" 2>&1
  if errorlevel 1 goto fail
)
echo Kontrollerer Qt og matematisk renderer ...
"%VPY%" -c "import PySide6, matplotlib, fitz; from PySide6.QtWidgets import QApplication; print(PySide6.__version__,matplotlib.__version__)" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo Installerer afhaengigheder. Foerste gang kan tage lidt tid ...
  echo Installerer requirements... >> "%LOG%"
  "%VPY%" -m pip install --disable-pip-version-check --only-binary=:all: -r "%~dp0requirements.txt" >> "%LOG%" 2>&1
  if errorlevel 1 (
    echo FEJL: Pakker kunne ikke installeres. Se logfilen.
    goto fail
  )
)
"%VPY%" -c "import PySide6, matplotlib, fitz; from PySide6.QtWidgets import QApplication; print('OK:',PySide6.__version__,matplotlib.__version__)" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo FEJL: Pakkerne kan ikke importeres efter installation. Se logfilen.
  goto fail
)
echo Starter vinduet ...
"%VPY%" "%~dp0run_app.py" >> "%LOG%" 2>&1
if errorlevel 1 goto fail
echo Appen lukkede normalt. >> "%LOG%"
exit /b 0
:fail
echo.
echo FEJL VED OPSTART. Send EM1_START_LOG.txt til ChatGPT.
echo Logfil: "%LOG%"
echo.
type "%LOG%"
echo.
pause
exit /b 1
