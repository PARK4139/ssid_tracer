@echo off
title %~1
set "PYTHONHOME="
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"
echo [%~1] cwd=%CD%
if defined SSID_TRACER_PYTHON_EXE (
    set "PYTHON_EXE=%SSID_TRACER_PYTHON_EXE%"
) else (
    set "PYTHON_EXE=python"
)
echo [%~1] python=%PYTHON_EXE%
"%PYTHON_EXE%" ensure_wifi_expected_ssids_watched.py --section %~1
echo [%~1] exited with %ERRORLEVEL%
