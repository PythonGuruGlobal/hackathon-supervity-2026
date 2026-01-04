@echo off
echo ========================================
echo  AI-Powered Market Intelligence System
echo ========================================
echo.
echo Starting AI Agentic Dashboard...
echo.
echo Dashboard will open at:
echo http://localhost:5002
echo.
echo Features:
echo - Automatic stock analysis
echo - ML-based forecasting
echo - Multi-signal AI agent
echo - Real-time alerts
echo - Profit/loss calculator
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

cd /d "%~dp0"
python agentic_system.py
