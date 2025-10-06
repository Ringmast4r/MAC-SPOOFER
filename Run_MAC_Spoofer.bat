@echo off
:: MAC Spoofer GUI Launcher
:: This script runs the MAC spoofer with administrator privileges

echo Starting MAC Address Spoofer GUI...
echo.
echo Note: This application requires administrator privileges to function properly.
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

:: Run the GUI application
python "%~dp0mac_spoofer_gui.py"

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
