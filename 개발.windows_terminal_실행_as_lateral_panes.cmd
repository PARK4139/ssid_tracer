@echo off
set "D=%~dp0"
if "%D:~-1%"=="\" set "D=%D:~0,-1%"
python "%D%\개발.windows_terminal_실행_as_lateral_panes.py"
