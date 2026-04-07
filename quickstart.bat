@echo off
REM Quick Start Guide for E-Commerce Tracker (Windows)

echo ==================================
echo E-Commerce Tracker - Quick Start
echo ==================================
echo.

REM Check Python version
echo [1/4] Checking Python version...
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [2/4] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
) else (
    echo [2/4] Activating virtual environment...
    call venv\Scripts\activate.bat
)
echo.

REM Install dependencies
echo [3/4] Installing dependencies...
pip install -r requirements.txt --quiet
playwright install --with-deps
echo.

REM Setup environment
echo [4/4] Setting up environment...
if not exist ".env" (
    copy .env.example .env
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Update .env file with your database credentials
echo   2. Start API: python -m uvicorn src.api.main:app --reload
echo   3. Or use Docker: docker-compose up -d
echo.
echo API Documentation: http://localhost:8000/docs
echo Database: PostgreSQL localhost:5432
echo.
