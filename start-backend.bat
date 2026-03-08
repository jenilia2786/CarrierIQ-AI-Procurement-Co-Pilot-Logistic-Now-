@echo off
echo ╔══════════════════════════════════════════════════════╗
echo ║         CarrierIQ Backend — Starting...             ║
echo ╚══════════════════════════════════════════════════════╝

cd /d "%~dp0backend"

REM Check if venv exists
if not exist venv (
    echo [1/3] Creating Python virtual environment...
    python -m venv venv
)

echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo [3/3] Starting FastAPI server on http://localhost:8000
echo.
echo 📌 API Docs: http://localhost:8000/docs
echo 📌 Frontend: Open frontend/index.html in browser
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
