@echo off
chcp 65001 >nul
cd /d "%~dp0"
set ARRANGE_DEV=1
"%~dp0venv\Scripts\python.exe" app_qt.py
