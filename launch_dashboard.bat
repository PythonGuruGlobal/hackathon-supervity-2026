@echo off
echo ========================================
echo  Market Alert Agent Dashboard
echo ========================================
echo.
echo Starting Streamlit dashboard...
echo.
echo The dashboard will open in your browser at:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.
echo ========================================
echo.

cd /d "%~dp0"
streamlit run dashboard.py
