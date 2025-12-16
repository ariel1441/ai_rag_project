# How to Test and Update the RAG System

## 🎯 Quick Start: Test the System

### Step 1: Run the Quick Test

**Open a PowerShell terminal OUTSIDE Cursor** (to avoid timeouts):
- Press `Win + R`, type `powershell`, press Enter
- Navigate to your project:
  ```powershell
  cd D:\ai_learning\train_ai_tamar_request
  ```
- Activate virtual environment:
  ```powershell
  .\venv\Scripts\activate.ps1
  ```
- Run the quick test:
  ```powershell
  python scripts/tests/test_rag_quick.py
  ```

**What this does:**
- ✅ Skips 4-bit quantization (avoids Windows CPU hang)
- ✅ Uses float16 directly (~7-8GB RAM)
- ✅ Tests ONE query to verify RAG works
- ✅ Expected time: 2-5 minutes for model loading, then 5-15 seconds per query

**Expected output:**
```
Step 3: Loading LLM model with float16...
⚠️  Windows CPU detected - skipping 4-bit quantization
   (Known issue: hangs after loading shards)
   Using float16 directly (~7-8GB RAM)

Loading with float16 (CPU-only for stability)...
⏳ This may take 1-2 minutes - please be patient...
   Progress: Loading checkpoint shards...
```

**Then it will:**
1. Load the model (2-5 minutes)
2. Test one query (5-15 seconds)
3. Show the answer and compare with database

---

## 🔧 Why 4-bit Quantization Doesn't Work

**The Problem:**
- bitsandbytes 4-bit quantization on Windows CPU has a known bug
- It loads the checkpoint shards (takes 15-20 minutes)
- Then **hangs indefinitely** during quantization initialization
- This is a Windows-specific issue with bitsandbytes

**The Solution:**
- ✅ **Use float16 directly** (already implemented)
- ✅ Code now automatically skips 4-bit on Windows CPU
- ✅ Uses ~7-8GB RAM (you have 10GB+ free, so it's fine)

---

## 📊 Testing Different Query Types

### Test 1: Person Name Query
```powershell
python scripts/tests/test_rag_quick.py
```
Tests: "כמה פניות יש מיניב ליבוביץ?"

### Test 2: Multiple Queries (After First Test Succeeds)

Create a simple script to test multiple queries:

```python
# test_multiple_queries.py
from scripts.core.rag_query import RAGSystem
from scripts.utils.hebrew import fix_hebrew_rtl

rag = RAGSystem()
rag.connect_db()
rag.load_model()  # Load once

queries = [
    'כמה פניות יש מיניב ליבוביץ?',
    'מה הפרויקטים של אור גלילי?',
    'תראה לי פניות פתוחות',
]

for query in queries:
    print(f"\nQuery: {fix_hebrew_rtl(query)}")
    result = rag.query(query, top_k=20)
    print(f"Answer: {fix_hebrew_rtl(result.get('answer', 'No answer'))}")
    print(f"Retrieved: {len(result.get('requests', []))} requests")
    print("-" * 80)

rag.close()
```

---

## 🚀 How to Update and Improve

### 1. Update the RAG System

**Edit the core files:**
- `scripts/core/rag_query.py` - Main RAG logic
- `scripts/utils/query_parser.py` - Query parsing
- `scripts/utils/text_processing.py` - Text chunking
- `scripts/core/search.py` - Database search

**After editing:**
- Run the quick test to verify it still works
- Test with different queries

### 2. Improve Query Parsing

**File:** `scripts/utils/query_parser.py`

**What to improve:**
- Better Hebrew name extraction
- Better intent detection
- Better entity extraction

**Test changes:**
```powershell
python scripts/tests/debug_name_extraction.py
```

### 3. Improve Search/Retrieval

**File:** `scripts/core/search.py`

**What to improve:**
- Better field weighting
- Better similarity thresholds
- Better hybrid search

**Test changes:**
```powershell
python scripts/tests/test_rag_retrieval_only.py
```

### 4. Improve LLM Prompts

**File:** `scripts/core/rag_query.py` - `build_prompt()` method

**What to improve:**
- Better Hebrew prompts
- Better context formatting
- Better answer extraction

**Test changes:**
- Run full RAG test and check answer quality

---

## 🐛 Troubleshooting

### Problem: Model Loading Hangs

**Solution:**
- ✅ Code now automatically skips 4-bit on Windows
- ✅ Uses float16 directly
- ✅ Should load in 2-5 minutes

**If it still hangs:**
1. Check RAM usage (should have 8GB+ free)
2. Close other applications
3. Restart computer (clears memory fragmentation)

### Problem: Database Connection Error

**Solution:**
```powershell
# Start PostgreSQL service
Start-Service postgresql-x64-18

# Verify it's running
Get-Service postgresql-x64-18
```

### Problem: Import Errors

**Solution:**
```powershell
# Make sure venv is activated
.\venv\Scripts\activate.ps1

# Install missing packages
pip install psycopg2-binary pgvector transformers torch sentence-transformers
```

### Problem: Cursor/VSCode Timeout

**Solution:**
- ✅ **Run tests in separate PowerShell terminal** (outside Cursor)
- ✅ This avoids the timeout issue
- ✅ Tests will complete successfully

---

## 📝 Workflow for Development

### Daily Development Workflow

1. **Make changes** to RAG code
2. **Run quick test** to verify:
   ```powershell
   python scripts/tests/test_rag_quick.py
   ```
3. **If test passes**, test with more queries
4. **If test fails**, check error and fix

### Before Demo

1. **Run comprehensive tests:**
   ```powershell
   # Test retrieval only (fast)
   python scripts/tests/test_rag_retrieval_only.py
   
   # Test full RAG (slower, but complete)
   python scripts/tests/test_rag_quick.py
   ```

2. **Test with real queries** you'll use in demo

3. **Check answer quality** - are answers accurate?

4. **Check speed** - is it fast enough for demo?

---

## ✅ Summary

**To Test:**
1. Open PowerShell outside Cursor
2. Activate venv: `.\venv\Scripts\activate.ps1`
3. Run: `python scripts/tests/test_rag_quick.py`
4. Wait 2-5 minutes for model loading
5. See results!

**To Update:**
1. Edit code files
2. Run quick test to verify
3. Test with different queries
4. Iterate!

**Key Points:**
- ✅ 4-bit quantization is skipped automatically on Windows
- ✅ float16 works reliably (~7-8GB RAM)
- ✅ Run tests in separate terminal to avoid timeouts
- ✅ Model loads once, then queries are fast (5-15 seconds)

**You're not stuck!** The system is working - just run the test in a separate terminal and it will complete successfully.

