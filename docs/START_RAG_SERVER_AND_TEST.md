# How to Start RAG Server and Test

## 🚀 Starting the API Server

### Step 1: Activate Virtual Environment
```powershell
# Navigate to project directory
cd D:\ai_learning\train_ai_tamar_request

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Step 2: Start the API Server
```powershell
# Start FastAPI server
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

**What this does:**
- Starts the API server on `http://localhost:8000`
- `--reload` enables auto-reload on code changes (for development)
- `--host 0.0.0.0` allows access from other devices on your network
- `--port 8000` uses port 8000 (default)

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Initializing search service...
INFO:     ✅ Search service initialized
INFO:     Initializing RAG service (no model loading yet)...
INFO:     ✅ RAG service initialized (model will load on first query)
INFO:     ✅ API server ready
INFO:     Application startup complete.
```

### Step 3: Verify Server is Running
Open your browser and go to:
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Web Interface:** http://localhost:8000/ (if frontend is served)

---

## 🌐 Accessing the Web Interface

### Option 1: Direct File Access
1. Open `api/frontend/index.html` in your browser
2. The frontend will connect to `http://localhost:8000` automatically

### Option 2: Via API Server (if configured)
If the API serves static files, go to:
- http://localhost:8000/

### Option 3: Manual API Testing
Use the interactive API docs at:
- http://localhost:8000/docs

---

## 🧪 Testing RAG Queries

### Via Web Interface:
1. Open the web interface (see above)
2. Enter your query in Hebrew
3. Select **"RAG - עם תשובה מלאה"** (Full RAG with answer)
4. Click search
5. Wait for the answer (first query will take longer as it loads the LLM model)

### Via API Directly:
```powershell
# Example: Test a person query
$body = @{
    query = "פניות מאור גלילי"
    include_details = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/rag" -Method POST -Body $body -ContentType "application/json"
```

### Via Python Script:
```powershell
# Run comprehensive test script
python scripts/tests/test_rag_comprehensive.py
```

---

## ⚡ GPU Detection

The system will automatically detect and use GPU if available.

**To verify GPU is being used:**
1. Check the terminal output when running RAG queries
2. Look for messages like:
   - `"Using device: cuda"`
   - `"GPU detected: NVIDIA GeForce RTX ..."`
3. First query will be slower (model loading), subsequent queries should be fast

**If GPU is not detected:**
- Check that CUDA is installed: `python -c "import torch; print(torch.cuda.is_available())"`
- Check that PyTorch was installed with CUDA support
- The system will fall back to CPU (slower but still works)

---

## 📋 Example Queries to Test

### Basic Find Queries:
- `פניות מאור גלילי`
- `בקשות מיניב ליבוביץ`
- `פניות מסוג 4`
- `בקשות בסטטוס 1`

### Count Queries:
- `כמה פניות יש מאור גלילי?`
- `כמה בקשות יש מסוג 4?`

### Summarize Queries:
- `תביא לי סיכום של כל הפניות מסוג 4`
- `תן לי סיכום של פניות מאור גלילי`

### Similar Requests:
- `תביא לי פניות דומות ל-211000001`
- `פניות דומות ל-211000226`

### Urgency Queries:
- `בקשות דחופות`
- `פניות דחופות מאור גלילי`

### Complex Queries:
- `תביא לי סיכום של פניות דחופות מאור גלילי מסוג 10`
- `כמה פניות יש מאור גלילי בסטטוס 1?`

---

## 🔍 Troubleshooting

### Server won't start:
- Check if port 8000 is already in use
- Verify database connection in `.env` file
- Check that PostgreSQL is running

### RAG queries are slow:
- First query is always slow (model loading)
- Check if GPU is being used (see above)
- CPU-only mode is slower but still functional

### No GPU detected:
- Install CUDA toolkit
- Reinstall PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu118`
- System will use CPU as fallback

### Answers don't make sense:
- Check that embeddings were generated correctly
- Verify database has data
- Check query parser output in terminal logs

---

## 📊 Performance Expectations

### With GPU:
- **First query:** 30-60 seconds (model loading)
- **Subsequent queries:** 3-10 seconds per query
- **Answer quality:** High (500 tokens, sampling)

### Without GPU (CPU only):
- **First query:** 60-120 seconds (model loading)
- **Subsequent queries:** 15-30 seconds per query
- **Answer quality:** Good (200 tokens, greedy decoding)

---

## 🎯 Next Steps

1. **Run comprehensive test script:**
   ```powershell
   python scripts/tests/test_rag_comprehensive.py
   ```

2. **Test manually via web interface:**
   - Try different query types
   - Verify answers are accurate
   - Check response times

3. **Monitor performance:**
   - Check GPU usage (Task Manager → Performance → GPU)
   - Monitor API logs for errors
   - Verify database query performance

---

## 📝 Notes

- The LLM model loads **lazily** (only when first RAG query is made)
- Search-only queries don't need the LLM (fast, ~3-5 seconds)
- Full RAG queries require the LLM (slower, but provides natural language answers)
- GPU usage is automatic if available
- All queries are logged in `api.log` file

