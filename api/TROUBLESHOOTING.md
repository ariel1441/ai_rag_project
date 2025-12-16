# API Troubleshooting Guide

## Port Already in Use Error

### Error Message
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): 
[winerror 10048] only one usage of each socket address (protocol/network address/port) is normally permitted
```

### Cause
Another process is already using port 8000.

### Solution

**Option 1: Use the helper script (Recommended)**
```powershell
.\api\start_server.ps1
```
This script automatically kills any process on port 8000 and starts the server.

**Option 2: Manual fix**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
Stop-Process -Id <PID> -Force

# Start server
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

**Option 3: Use a different port**
```powershell
python -m uvicorn api.app:app --host 127.0.0.1 --port 8001
```
Then update `api/frontend/app.js` to use port 8001.

---

## Server Won't Start

### Check Database Connection
Make sure PostgreSQL is running:
```powershell
Get-Service postgresql-x64-18
```

If not running:
```powershell
Start-Service postgresql-x64-18
```

### Check Dependencies
```powershell
pip install -r api/requirements.txt
```

---

## Frontend Can't Connect to API

### Check CORS
The API should allow CORS from localhost. Check `api/app.py` for CORS configuration.

### Check API URL
Make sure `api/frontend/app.js` has the correct API URL:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Check Server is Running
```powershell
# Test health endpoint
curl http://localhost:8000/api/health
```

---

## Tests Fail

### Run Tests
```powershell
python api/test_api.py
```

### Check Server is Running
Tests require the server to be running. Start it first:
```powershell
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

---

## Common Issues

1. **Port in use** → Use `start_server.ps1` or kill process manually
2. **Database not running** → Start PostgreSQL service
3. **Dependencies missing** → Run `pip install -r api/requirements.txt`
4. **CORS errors** → Check CORS configuration in `api/app.py`
5. **Frontend can't connect** → Check API URL and server status

