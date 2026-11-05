@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "EM1_ENV=%LOCALAPPDATA%\EM1\desktop-python313-20261105"
set "EM1_PY=%EM1_ENV%\Scripts\python.exe"
py -3.13 -c "import sys,struct,sysconfig; assert sys.version_info[:2] == (3,13) and struct.calcsize('P') == 8 and sysconfig.get_platform() == 'win-amd64' and not sysconfig.get_config_var('Py_GIL_DISABLED')" >nul 2>&1
if errorlevel 1 (
 echo Install Python 3.13 x64 with the py launcher first. See WINDOWS_INTEGRATED.md.
 pause
 exit /b 1
)
if not exist "%EM1_PY%" (
 py -3.13 -m venv "%EM1_ENV%"
 if errorlevel 1 goto fail
)
"%EM1_PY%" -c "import sys,struct,sysconfig; assert sys.version_info[:2] == (3,13) and struct.calcsize('P') == 8 and sysconfig.get_platform() == 'win-amd64' and not sysconfig.get_config_var('Py_GIL_DISABLED')"
if errorlevel 1 goto fail
if exist "%~dp0wheelhouse\*.whl" (
 "%EM1_PY%" -m pip install --no-index --find-links="%~dp0wheelhouse" -r "%~dp0requirements-windows-lock.txt"
) else (
 echo First installation needs internet. Runtime does not.
 "%EM1_PY%" -m pip install --only-binary=:all: -r "%~dp0requirements-windows-lock.txt"
)
if errorlevel 1 goto fail
"%EM1_PY%" -m pip check
if errorlevel 1 goto fail
"%EM1_PY%" -c "import PySide6, matplotlib, fitz; from backend_paths import location; import sys; sys.path.insert(0,str(location(True)[0])); from em1_solver.assisted_backend import catalog; assert len(catalog()['models']) >= 8; print('Installation OK')"
if errorlevel 1 goto fail
echo Ready. Double-click START_WINDOWS.bat. No backend download is needed.
pause
exit /b 0
:fail
echo Installation failed. Do not remove your old app. Read WINDOWS_INTEGRATED.md.
pause
exit /b 1
