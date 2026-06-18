@echo off
title %~1
set "PYTHONHOME="
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "VIRTUAL_ENV=%ROOT%\.venv"
set "PATH=%ROOT%\.venv\Scripts;%PATH%"
cd /d "%ROOT%"
echo [%~1] cwd=%CD%
if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
    set "PYTHON_EXE=%VIRTUAL_ENV%\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)
echo [%~1] python=%PYTHON_EXE%
"%PYTHON_EXE%" ensure_wifi_expected_ssids_watched.py --section %~1
echo [%~1] exited with %ERRORLEVEL%
