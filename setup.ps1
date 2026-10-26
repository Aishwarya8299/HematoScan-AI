# Hematoscan — one-time setup (run once)
# Right-click → "Run with PowerShell"  OR  open PowerShell here and run: .\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "`n=== Hematoscan Setup ===" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/4] Checking Python..." -ForegroundColor Yellow
$python = $null
foreach ($cmd in @("python", "py", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $ver -match "Python") {
            $python = $cmd
            Write-Host "  Found: $ver (via '$cmd')" -ForegroundColor Green
            break
        }
    } catch { }
}

if (-not $python) {
    Write-Host "`nERROR: Python not found." -ForegroundColor Red
    Write-Host "Install Python 3.11+ from https://www.python.org/downloads/"
    Write-Host "Check 'Add python.exe to PATH' during install, then run this script again."
    Read-Host "`nPress Enter to exit"
    exit 1
}

# 2. .env file
Write-Host "`n[2/4] Environment file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "  .env already exists" -ForegroundColor Green
}

# 3. Virtual environment
Write-Host "`n[3/4] Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $python -m venv .venv
    Write-Host "  Created .venv" -ForegroundColor Green
} else {
    Write-Host "  .venv already exists" -ForegroundColor Green
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

# 4. Install dependencies
Write-Host "`n[4/4] Installing dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r backend\requirements.txt

# Verify uvicorn
& $venvPython -c "import uvicorn; print('  uvicorn', uvicorn.__version__, 'OK')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: uvicorn failed to install." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Cyan
Write-Host "Next: double-click start-server.bat  OR  run .\start-server.ps1"
Write-Host "Then open: http://localhost:8000/api/v1/system/health`n"
Read-Host "Press Enter to exit"
