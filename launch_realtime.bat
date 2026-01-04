@echo off
echo ====================================
echo  Real-Time Stock Market Dashboard
echo ====================================
echo.
echo Starting real-time dashboard...
echo Press Ctrl+C to stop
echo.

streamlit run realtime_dashboard.py --server.port 8502

pause
