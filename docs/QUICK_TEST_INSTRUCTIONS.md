# Quick Test Instructions

## To Run Comprehensive RAG Tests

**IMPORTANT:** Run in a **separate PowerShell terminal** (not in Cursor) to avoid timeouts.

### Step 1: Open Separate Terminal

Open a new PowerShell window (outside Cursor).

### Step 2: Navigate and Activate

```powershell
cd D:\ai_learning\train_ai_tamar_request
.\venv\Scripts\activate.ps1
```

### Step 3: Run Tests

```powershell
python scripts/tests/test_rag_standalone_comprehensive.py
```

### What It Tests

1. ✅ **Functionality:** 8 different query types (count, find, summarize)
2. ✅ **Speed:** Measures first load vs subsequent queries
3. ✅ **Accuracy:** Compares answers with database counts
4. ✅ **Retrieval:** Verifies retrieved IDs match expected

### Expected Results

- **First model load:** 30-60 seconds (happens once per session)
- **Subsequent queries:** 5-15 seconds each (fast, model in memory)
- **Accuracy:** Counts should match database (exact or within 2)
- **Retrieval:** Retrieved IDs should match database sample

### Results Saved

Test results are saved to `test_results_data.json` for analysis.

---

## Design Review Summary

✅ **All design decisions are correct:**
- Chunk size: 512 (standard) ✅
- Chunk overlap: 50 (standard) ✅
- Top-K: 20 (reasonable) ✅
- Embedding model: all-MiniLM-L6-v2 (excellent) ✅
- LLM model: Mistral-7B-Instruct (good for Hebrew) ✅
- Field weighting: Excellent design ✅
- Hybrid search: Excellent design ✅

**See `COMPREHENSIVE_RAG_TESTING_AND_DESIGN_REVIEW_FINAL.md` for full details.**

