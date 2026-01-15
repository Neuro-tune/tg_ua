@echo off
chcp 65001 > nul
title Client Booking Bot (DO NOT CLOSE)
color 0B

echo ==========================================
echo        STARTING BOT...
echo ==========================================
echo.

:: Check if venv folder exists
if not exist venv (
    color 0C
    echo ERROR: Virtual environment not found!
    echo Run install.bat first
    pause
    exit
)

call venv\Scripts\activate

:: Run module
python -m bot.main

:: If bot crashes, window won't close immediately
echo.
echo ==========================================
echo    BOT STOPPED.
echo ==========================================
pause