@echo off
setlocal
cd /d "%~dp0"

cls
echo ================================================================
echo           YouTube Opus Downloader V6
echo           Chrome + cookies.txt mode
echo ================================================================
echo.
python youtube_opus_server.py

if errorlevel 1 echo [ERROR] Service exited abnormally.
pause
endlocal
