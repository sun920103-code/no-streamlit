@echo off
title No Streamlit - Startup

echo ============================================
echo    No Streamlit Quant Platform
echo ============================================
echo.

:: Kill any ghost processes on port 8002
echo [1/2] Cleaning up ghost processes and starting backend service (FastAPI :8002) ...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002 " ^| findstr "LISTENING"') do (
    echo Terminating ghost backend process (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: Start Backend (FastAPI)
start "Backend - FastAPI" cmd /k "cd /d d:\No Streamlit\backend && ..\.venv\Scripts\uvicorn.exe main:app --reload --port 8002"

:: Wait for backend to initialize
timeout /t 4 /nobreak >nul

:: Start Frontend (Vite)
echo [2/2] Starting frontend service (Vite :5173) ...
start "Frontend - Vue3" cmd /k "cd /d d:\No Streamlit\frontend && npx vite"

:: Wait for frontend to initialize
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo    All services started!
echo.
echo    Frontend:  http://localhost:5173
echo    Backend:   http://localhost:8002/api/docs
echo.
echo    To exit: just close the two popup command windows
echo ============================================
echo.

:: Automatically open browser
start http://localhost:5173

pause
