# Kill any process using port 8000
Write-Host "Killing processes on port 8000..." -ForegroundColor Yellow

$ports = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($ports) {
    $processIds = $ports | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Killing process $processId ($($process.ProcessName))..." -ForegroundColor Yellow
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
    
    # Verify
    $stillInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($stillInUse) {
        Write-Host "⚠️  Some processes may still be using the port" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Port 8000 is now free" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Port 8000 is already free" -ForegroundColor Green
}

