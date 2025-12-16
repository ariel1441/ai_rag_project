# Testing API Locally on Your PC

## ✅ Yes, You Can Test on Your PC!

**The API is designed for server deployment, but works perfectly for local testing.**

**What this means:**
- ✅ Run API on your PC
- ✅ Test with Postman, curl, or browser
- ✅ Same code works on server later
- ✅ Model loads once, can test multiple queries

---

## 🚀 Quick Start

### 1. Install API Dependencies

```powershell
pip install -r api/requirements.txt
```

### 2. Run API Server

```powershell
cd api
python app.py
```

Or from project root:
```powershell
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
```

**You'll see:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
✅ Search service initialized
✅ RAG service initialized (model will load on first query)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Test in Browser

Open: `http://localhost:8000/api/health`

Should show:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "search_system": "ready",
  "rag_system": "lazy loading"
}
```

### 4. Test Search (No LLM Needed)

**Using curl:**
```powershell
curl -X POST http://localhost:8000/api/search `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"פניות מאור גלילי\", \"top_k\": 10}'
```

**Using PowerShell:**
```powershell
$body = @{
    query = "פניות מאור גלילי"
    top_k = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/search" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**This works immediately** - no model loading needed!

### 5. Test RAG (Retrieval Only - Fast)

```powershell
$body = @{
    query = "כמה פניות יש מיניב ליבוביץ?"
    use_llm = $false
    top_k = 20
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/rag/query" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**This also works immediately** - returns retrieval only (no LLM).

### 6. Test Full RAG (With LLM - Slow First Time)

```powershell
$body = @{
    query = "כמה פניות יש מיניב ליבוביץ?"
    use_llm = $true
    top_k = 20
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/rag/query" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**First query:** Takes 2-5 minutes (loads model)  
**Subsequent queries:** 5-15 seconds (model cached)

---

## 🔄 Local vs Server

**Local Testing (Your PC):**
- ✅ Same code
- ✅ Same functionality
- ✅ Model loads once (like server)
- ✅ Can test everything
- ⚠️ Only you can access (localhost)

**Server Deployment:**
- ✅ Multiple users can access
- ✅ Runs 24/7
- ✅ Internal network access
- ✅ Production ready

**The code is the same!** Just deploy to server when ready.

---

## 📝 Testing Checklist

- [ ] API server starts
- [ ] Health check works
- [ ] Search endpoint works (no LLM)
- [ ] RAG endpoint works with `use_llm=false`
- [ ] RAG endpoint works with `use_llm=true` (after model loads)
- [ ] Error handling works
- [ ] Hebrew text displays correctly

---

## 🎯 Next: Build Frontend

Once API works, build a simple web interface:
- HTML + JavaScript
- Connects to your local API
- Can deploy to server later

