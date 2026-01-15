@echo off
chcp 65001 > nul
title Bot Installation (First Run)
color 0A

echo ==========================================
echo    SETTING UP CLIENT BOOKING BOT
echo ==========================================
echo.
echo 1. Creating virtual environment...
python -m venv venv

echo.
echo 2. Activating environment...
call venv\Scripts\activate

echo.
echo 3. Updating pip...
python -m pip install --upgrade pip

echo.
echo 4. Installing libraries (this may take time)...
pip install -r requirements.txt

echo.
echo ==========================================
echo    INSTALLATION SUCCESSFULLY COMPLETED!
echo ==========================================
echo.
echo Now you can run the bot via start.bat
echo.
pause