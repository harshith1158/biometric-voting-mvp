@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo  TRUE VOTE - System Startup
echo ========================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Reset Database
echo [1/4] Resetting database...
cd backend
python reset_db.py
if errorlevel 1 (
    echo ERROR: Database reset failed
    pause
    exit /b 1
)
cd ..
echo [OK] Database reset successful

echo.
echo [2/4] Starting Backend Server (Safe Mode)...
start "TRUE VOTE - Backend (5000)" cmd /k python backend/run_safe.py
timeout /t 3 /nobreak

echo [3/4] Starting Frontend - Admin (5173)...
cd truevote-frontend
start "TRUE VOTE - Frontend Admin (5173)" cmd /k npm run dev
cd ..
timeout /t 3 /nobreak

echo.
echo ========================================
echo  System Started Successfully!
echo ========================================
echo.
echo Backend:    http://localhost:5000
echo Frontend:   http://localhost:5173
echo.
echo Press Ctrl+C in any window to stop services
echo ========================================
echo.

pause
