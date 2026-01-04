@echo off
REM MedGuard Local Setup Script for Windows

echo ============================================================
echo MedGuard Local Setup
echo ============================================================
echo.

REM Check if virtual environment is activated
python -c "import sys; exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Step 1: Installing dependencies...
echo ------------------------------------------------------------
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Checking setup...
echo ------------------------------------------------------------
python check_setup.py
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Some checks failed. Please review the output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Set your OpenAI API key:
echo    set OPENAI_API_KEY=your-api-key-here
echo.
echo 2. Run data ingestion (first time only):
echo    python ingest_cloud_embeddings.py --limit-partitions 1
echo.
echo 3. Start the API server:
echo    uvicorn app.main:app --reload
echo.
pause


