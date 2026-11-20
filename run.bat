@echo off
setlocal
echo ============================================================
echo   PRIVASCOPE - Privacy-First Observability ^& AIOps Platform
echo ============================================================

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

echo [INFO] Installing/verifying dependencies...
.venv\Scripts\python.exe -m pip install -q -r requirements.txt

echo [INFO] Launching PRIVASCOPE on http://localhost:8501 ...
.venv\Scripts\python.exe -m streamlit run app.py
pause
