# Quick Start Guide

## If Server Crashes Immediately

### Step 1: Test Startup
```powershell
python api/test_startup.py
```

This will show you exactly what's failing.

### Step 2: Start Server Manually
```powershell
# Activate venv
.\venv\Scripts\activate.ps1

# Start server
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

### Step 3: If It Still Crashes

**Check the error message** - it will tell you what's wrong:
- Database connection error? → Check PostgreSQL is running
- Import error? → Run `pip install -r api/requirements.txt`
- Memory error? → Close other apps, restart computer

### Step 4: Use Safe Script
```powershell
.\api\start_server_safe.ps1
```

This script will show errors before closing.

---

## Common Issues

### Port Already in Use
```powershell
# Kill process on port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
# Then: Stop-Process -Id <PID> -Force
```

### Database Not Running
```powershell
Start-Service postgresql-x64-18
```

### Import Errors
```powershell
pip install -r api/requirements.txt
```

---

## Normal Startup

If everything works, you should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
✅ Search service initialized
✅ RAG service initialized (model will load on first query)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Then open: `http://localhost:8000/api/health` to test.

