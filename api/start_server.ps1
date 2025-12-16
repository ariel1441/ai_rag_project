# Start API Server Script
# Kills any existing process on port 8000 and starts the server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting API Server" -ForegroundColor Cyan
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
Write-Host "Testing startup first..." -ForegroundColor Yellow
python api/test_startup.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Startup test failed! Fix errors above before starting server." -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Write-Host "Starting API server on http://127.0.0.1:8000..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "If the server crashes, check the error message above." -ForegroundColor Yellow
Write-Host ""

# Start server - catch errors
try {
    python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "SERVER CRASHED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
