@echo off
setlocal
cd /d "%~dp0"
title LunArk: Genesis

echo ========================================================
echo        LunArk: Genesis - Moon-Base Management
echo     NASA Space Apps Challenge 2026 - Team LunArk
echo ========================================================
echo.
echo Welcome Commander! Preparing lunar outpost environment...
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo Please install Python 3.11 or newer and check "Add Python to PATH".
    pause
    exit /b 1
)

if exist ".venv\Scripts\activate.bat" goto activate_env

echo [*] Creating virtual environment .venv ...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment .venv.
    pause
    exit /b 1
)

:activate_env
echo [*] Activating virtual environment and verifying requirements...
call .venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

echo.
echo [*] Launching LunArk: Genesis...
echo ========================================================
echo.
python main.py
if errorlevel 1 (
    echo.
    echo [!] The game exited with an error.
    pause
)

endlocal
