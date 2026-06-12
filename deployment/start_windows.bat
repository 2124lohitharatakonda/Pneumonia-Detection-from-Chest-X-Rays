@echo off
REM ============================================================
REM PneumoDetect — Windows Production Start Script (Waitress)
REM Run from project root: deployment\start_windows.bat
REM ============================================================

echo Starting PneumoDetect with Waitress...
cd /d "%~dp0\.."

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Run setup first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if not exist ".env" (
    echo ERROR: .env file not found. Copy .env.example to .env and fill in values.
    pause
    exit /b 1
)

set FLASK_ENV=production
waitress-serve --port=5000 --threads=4 wsgi:app
pause
