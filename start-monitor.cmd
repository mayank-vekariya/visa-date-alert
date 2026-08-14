@echo off
cd /d "%~dp0"
".venv\Scripts\visa-alert.exe" run
if errorlevel 1 pause
