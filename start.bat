@echo off
chcp 65001 >nul 2>&1
title No Streamlit - Startup

echo ============================================
echo    No Streamlit Quant Platform
echo ============================================
echo.

set "ROOT=%~dp0"

echo [1/2] Starting backend (FastAPI :8002) ...
start "Backend - FastAPI" /d "%ROOT%backend" cmd /k ..\.venv\Scripts\uvicorn.exe main:app --reload --port 8002
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