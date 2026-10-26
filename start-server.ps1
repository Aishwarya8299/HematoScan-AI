# Hematoscan — start the API server (keep this window open)
# Run: .\start-server.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

Write-Host "`n=== Hematoscan API Server ===" -ForegroundColor Cyan

if (-not (Test-Path $Python)) {
    Write-Host "Virtual environment not found at $Python" -ForegroundColor Red
    Write-Host "Run setup.bat first (one-time)." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

# Verify uvicorn is installed in the venv
& $Python -c "import uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "uvicorn not installed. Running pip install..." -ForegroundColor Yellow
    & $Python -m pip install -r (Join-Path $Root "backend\requirements.txt")
}

Write-Host "`nStarting server at http://localhost:8000" -ForegroundColor Green
Write-Host "  Health: http://localhost:8000/api/v1/system/health"
Write-Host "  Docs:   http://localhost:8000/docs"
Write-Host "`nPress Ctrl+C to stop.`n" -ForegroundColor DarkGray

Set-Location (Join-Path $Root "backend")

# python -m uvicorn works reliably on Windows (no uvicorn.exe path needed)
& $Python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
