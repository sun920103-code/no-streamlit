@echo off
chcp 65001 >nul 2>&1
title No Streamlit - Startup

:: Force Python to use UTF-8 encoding to prevent Emoji UnicodeEncodeError
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo ============================================
echo    No Streamlit Quant Platform
echo ============================================
echo.

set "ROOT=%~dp0"

:: Clean stale processes
echo [0/2] Cleaning stale processes...
taskkill /FI "WINDOWTITLE eq Backend - FastAPI" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend - Vue3" /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8002 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo   Done.
echo.

echo [1/2] Starting backend (FastAPI :8002) ...
start "Backend - FastAPI" /d "%ROOT%backend" cmd /k "%ROOT%.venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8002
timeout /t 4 /nobreak >nul

echo [2/2] Starting frontend (Vite :5173) ...
start "Frontend - Vue3" /d "%ROOT%frontend" cmd /k npx vite
timeout /t 6 /nobreak >nul

echo.
echo ============================================
echo    All services started!
echo    Frontend:  http://localhost:5173
echo    Backend:   http://localhost:8002/api/docs
echo ============================================
echo.

start "" http://localhost:5173
pause