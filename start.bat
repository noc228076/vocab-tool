@echo off
title CET Vocabulary Tool
echo ========================================
echo    CET 4/6 Vocabulary Tool
echo ========================================
echo.
echo Starting application...
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found.
    echo Please install Python 3.7+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist "venv" (
    echo First run, creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo App started! Check system tray.
echo Right-click tray icon to start learning.
echo.
pythonw run.py

if errorlevel 1 (
    echo.
    echo Launch failed, trying python instead...
    python run.py
)

pause
