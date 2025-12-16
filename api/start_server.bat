@echo off
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
echo.
echo ========================================
echo Starting API Server
echo ========================================
echo.

REM Kill any process using port 8000
echo Checking for processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Found process %%a using port 8000, killing it...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo Port 8000 should be free now.
echo.

echo Testing startup first...
python api/test_startup.py
if errorlevel 1 (
    echo.
    echo ERROR: Startup test failed!
    echo Check the error above.
    echo.
    pause
    exit /b 1
)
echo.
echo Starting server...
echo If it crashes, you'll see the error below.
echo Press Ctrl+C to stop the server.
echo.
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
if errorlevel 1 (
    echo.
    echo ========================================
    echo SERVER STOPPED
    echo ========================================
    echo.
    echo Check the error message above.
    echo.
)
pause

