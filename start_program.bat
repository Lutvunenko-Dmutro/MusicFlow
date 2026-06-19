@echo off
title YouTube Music Pro
color 0b

echo ===================================================
echo       Preparing YouTube Music Pro...
echo ===================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python and check "Add python.exe to PATH".
    pause
    exit /b
)

echo Starting program...
python main.py
pause
