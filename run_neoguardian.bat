@echo off
setlocal enabledelayedexpansion
title NeoGuardian -- AI Neonatal Monitoring and Early Warning System
color 0b

echo ======================================================================
echo    NEOGUARDIAN: AI-BASED NEONATAL HEALTH MONITORING AND EARLY WARNING
echo ======================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    color 0c
    echo [ERROR] Python virtual environment was not found at .venv\Scripts\python.exe
    echo Please make sure the .venv directory is present.
    echo.
    pause
    exit /b 1
)

echo [1/3] Starting server...
echo       Launching FastAPI + React UI on http://127.0.0.1:8000 ...

:: Change directory to backend so uvicorn imports app.main:app correctly
cd backend

:: Start uvicorn in the background attached to this console
start /b "" "..\\.venv\\Scripts\\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo [2/3] Waiting for backend...
powershell -NoProfile -Command "$ready = $false; for ($i=0; $i -lt 30; $i++) { try { $res = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 1; if ($res.status -eq 'HEALTHY') { $ready = $true; break } } catch { Start-Sleep -Milliseconds 600 } }; if (-not $ready) { exit 1 }"

if %ERRORLEVEL% NEQ 0 (
    color 0c
    echo.
    echo [ERROR] Server failed to respond within 20 seconds.
    echo Please review the startup log above.
    pause
    exit /b 1
)

echo [3/3] Opening NeoGuardian...
start http://127.0.0.1:8000/

echo.
echo ======================================================================
echo   NEOGUARDIAN IS LIVE AT: http://127.0.0.1:8000/
echo   Swagger OpenAPI Docs:   http://127.0.0.1:8000/docs
echo.
echo   Press Ctrl+C or close this window anytime to stop the server.
echo ======================================================================
echo.

:: Keep window open and stream uvicorn log output
pause >nul
