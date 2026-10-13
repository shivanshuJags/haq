# Start Haq locally: backend (FastAPI :8000) and frontend (Vite :5173), each in its own window.
#
# Run from the project folder:
#     powershell -ExecutionPolicy Bypass -File dev.ps1
#
# Close a server with Ctrl+C in its window (or just close the window).

$root = $PSScriptRoot

# Refuse to start twice — a leftover server on the same port causes confusing errors
foreach ($port in 8000, 5173) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "Port $port is already in use - is Haq already running? Close that window first." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; `$host.UI.RawUI.WindowTitle = 'Haq backend'; .\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000"

Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\web'; `$host.UI.RawUI.WindowTitle = 'Haq frontend'; npm run dev"

# The backend loads ~1,000 schemes into memory at startup (~10s); wait for it before opening the app
Write-Host "Waiting for the backend to load schemes..." -ForegroundColor Cyan
for ($i = 0; $i -lt 60; $i++) {
    try {
        Invoke-RestMethod "http://localhost:8000/api/health" -TimeoutSec 2 | Out-Null
        Write-Host "Ready! Opening http://localhost:5173" -ForegroundColor Green
        Start-Process "http://localhost:5173"
        exit 0
    } catch {
        Start-Sleep -Seconds 1
    }
}
Write-Host "Backend did not start in 60s - check the 'Haq backend' window for the error." -ForegroundColor Red
exit 1
