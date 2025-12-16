# Python 3.13 Setup Script
# Run this AFTER installing Python 3.13 from python.org

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Python 3.13 Setup for 4-bit Quantization" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python 3.13 is available
Write-Host "Checking for Python 3.13..." -ForegroundColor Yellow
try {
    $python313 = py -3.13 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Found: $python313" -ForegroundColor Green
    } else {
        Write-Host "❌ Python 3.13 not found!" -ForegroundColor Red
        Write-Host "Please install Python 3.13 from: https://www.python.org/downloads/release/python-3131/" -ForegroundColor Yellow
        Write-Host "Make sure to check 'Add Python 3.13 to PATH' during installation." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Python 3.13 not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.13 from: https://www.python.org/downloads/release/python-3131/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Navigate to project directory
$projectDir = "D:\ai_learning\train_ai_tamar_request"
if (-not (Test-Path $projectDir)) {
    Write-Host "❌ Project directory not found: $projectDir" -ForegroundColor Red
    exit 1
}

Set-Location $projectDir
Write-Host "Project directory: $projectDir" -ForegroundColor Cyan
Write-Host ""

# Create virtual environment
$venvPath = "venv313"
if (Test-Path $venvPath) {
    Write-Host "⚠️  Virtual environment already exists: $venvPath" -ForegroundColor Yellow
    $response = Read-Host "Delete and recreate? (y/n)"
    if ($response -eq 'y') {
        Remove-Item -Recurse -Force $venvPath
        Write-Host "Deleted old virtual environment" -ForegroundColor Yellow
    } else {
        Write-Host "Using existing virtual environment" -ForegroundColor Cyan
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment with Python 3.13..." -ForegroundColor Yellow
    py -3.13 -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Activation failed. Trying to set execution policy..." -ForegroundColor Yellow
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    & "$venvPath\Scripts\Activate.ps1"
}

Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "✅ Pip upgraded" -ForegroundColor Green
Write-Host ""

# Install requirements
Write-Host "Installing packages from requirements.txt..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ All packages installed successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Verify bitsandbytes
    Write-Host "Verifying bitsandbytes installation..." -ForegroundColor Yellow
    python -c "import bitsandbytes; print('✅ bitsandbytes version:', bitsandbytes.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ bitsandbytes is ready for 4-bit quantization!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  bitsandbytes verification failed" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Test model loading: python scripts/tests/test_model_loading_only.py" -ForegroundColor White
    Write-Host "2. Run full RAG tests: python scripts/tests/test_rag_comprehensive_final.py" -ForegroundColor White
    Write-Host ""
    Write-Host "To activate this environment in the future:" -ForegroundColor Yellow
    Write-Host "  .\venv313\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Package installation failed" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Yellow
    exit 1
}

