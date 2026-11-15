@echo off
setlocal
title LunArk: Genesis

echo ========================================================
echo        LunArk: Genesis - Moon-Base Management
echo     NASA Space Apps Challenge 2026 - Team LunArk
echo ========================================================
echo.
echo Welcome Commander! Preparing lunar outpost environment...
echo.

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo.
echo [*] Launching LunArk: Genesis...
echo ========================================================
echo.
python main.py

call deactivate
endlocal
