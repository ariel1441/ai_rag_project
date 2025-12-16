# Safe Start API Server Script
# Catches errors and shows them before closing

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting API Server (Safe Mode)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "Project root: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Check for existing server and kill it
Write-Host "Checking for existing server on port 8000..." -ForegroundColor Yellow
$ports = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($ports) {
    $processIds = $ports | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Found process $processId ($($process.ProcessName)) using port 8000, stopping it..." -ForegroundColor Yellow
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Waiting for port to be released..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # Verify port is free
    $stillInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($stillInUse) {
        Write-Host "⚠️  Port still in use, trying harder..." -ForegroundColor Yellow
        $processIds = $stillInUse | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($processId in $processIds) {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    Write-Host "✅ Port 8000 should be free now" -ForegroundColor Green
} else {
    Write-Host "✅ Port 8000 is free" -ForegroundColor Green
}

Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\activate.ps1"

Write-Host ""
Write-Host "Starting API server..." -ForegroundColor Green
Write-Host "If there's an error, it will be shown below:" -ForegroundColor Yellow
Write-Host ""

# Try to start server and catch errors
try {
    python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR STARTING SERVER" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Full error:" -ForegroundColor Yellow
    Write-Host $_.Exception -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

