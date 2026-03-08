@echo off
setlocal

:: =====================================================================
:: CarrierIQ Launcher — Multi-Terminal Mode
:: =====================================================================

title CarrierIQ Launcher

echo ---------------------------------------------------------
echo [CARRIER-IQ] Starting CarrierIQ Project in Separate Terminals...
echo ---------------------------------------------------------
echo.

:: 1. Start Backend Terminal
echo [*] Launching Backend Server (Port 8000)...
start "CarrierIQ Backend" cmd /k "echo === CarrierIQ Backend Server === && cd backend && (if not exist venv311 (echo Creating venv... && py -3.11 -m venv venv311)) && call venv311\Scripts\activate.bat && pip install -r requirements.txt -q && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: 2. Start Frontend Terminal
echo [*] Launching Frontend Server (Port 3000)...
start "CarrierIQ Frontend" cmd /k "echo === CarrierIQ Frontend Server === && cd frontend && echo Serving at http://localhost:3000 && python -m http.server 3000"

echo.
echo ---------------------------------------------------------
echo [OK] Successfully launched both services!
echo.
echo - Backend API: http://localhost:8000
echo - API Docs:    http://localhost:8000/docs
echo - Web App:     http://localhost:3000
echo ---------------------------------------------------------
echo.
echo You can now close this launcher window.
pause
