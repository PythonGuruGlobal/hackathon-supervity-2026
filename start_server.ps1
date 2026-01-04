# Start MedGuard Server with Conda Environment
# Usage: .\start_server.ps1

Write-Host "Starting MedGuard API server with medguard conda environment..." -ForegroundColor Cyan

# Use conda run to execute commands in the medguard environment
conda run -n medguard uvicorn app.main:app --reload

