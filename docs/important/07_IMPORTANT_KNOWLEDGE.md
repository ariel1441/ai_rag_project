# Important Knowledge - Key Concepts and Gotchas

**Essential concepts, common pitfalls, best practices, and important limitations you should know**

---

## 📋 Table of Contents

1. [Key Concepts](#key-concepts)
2. [Common Gotchas](#common-gotchas)
3. [Best Practices](#best-practices)
4. [Important Limitations](#important-limitations)
5. [What to Know Before Making Changes](#what-to-know-before-making-changes)

---

## Key Concepts

### Embeddings vs RAG Models

**Two Different Models:**

1. **Embedding Model** (sentence-transformers/all-MiniLM-L6-v2):
   - **Purpose:** Convert text → numbers (vectors) for search
   - **Size:** ~500MB
   - **Speed:** Very fast (milliseconds)
   - **Always loaded:** Yes (lightweight)
   - **Used in:** All search types (1, 2, 3)
   - **Output:** 384-dimensional vector

2. **LLM Model** (Mistral-7B-Instruct):
   - **Purpose:** Generate natural language answers
   - **Size:** ~4GB (4-bit) or ~7-8GB (float16)
   - **Speed:** Slow first time (loads model), fast after
   - **Always loaded:** No (lazy loading)
   - **Used in:** Type 3 only (Full RAG)
   - **Output:** Natural language text

**Key Point:** The embedding model is NOT the RAG model - they're two different things!

---

### Semantic Search vs Exact Match

**Semantic Search:**
- Finds by meaning, not just keywords
- "פניות מיניב" finds "יניב ליבוביץ" requests
- More flexible, finds variations
- Counts may differ from exact SQL LIKE counts

**Exact Match:**
- SQL `LIKE '%text%'` - exact text only
- More restrictive
- Perfect counts
- May miss variations

**We use semantic search** because it's more flexible and finds relevant results even with variations.

---

### Field Weighting

**Why weight fields?**
- Important fields appear more in embeddings
- Model learns they're important
- Better search results

**How it works:**
- Weight 3.0x: Repeat 3 times (most important)
- Weight 2.0x: Repeat 2 times (important)
- Weight 1.0x: Include once (supporting)
- Weight 0.5x: Include once (specific queries)

**Key Point:** We customize the INPUT (field weighting), not the model itself.

---

### Chunking Strategy

**Why chunk?**
- Embedding models work best with focused text
- Better semantic meaning per chunk
- Faster processing
- Better search results

**Current settings:**
- Chunk size: 512 characters (standard practice)
- Overlap: 50 characters (~10% overlap)
- Max chunks: 100 per request (safety limit)

**Why overlap?**
- Prevents losing context at chunk boundaries
- If "Project: אלינור" is split between chunks, overlap ensures it appears in both

---

### Similarity Thresholds

**Purpose:** Filter low-relevance results from total count.

**Current thresholds:**
- Person/Project queries: 0.5 (50% similarity)
- General queries: 0.4 (40% similarity)
- Filtered queries: No threshold (uses filter only)

**Why different thresholds?**
- Person/project queries are more specific → higher threshold
- General queries are broader → lower threshold
- Filtered queries are exact → no threshold needed

**Important:** Semantic search counts will differ from exact SQL LIKE counts. This is expected behavior.

---

## Common Gotchas

### 1. Model Loading Crashes

**Problem:** Process crashes at 0% or 33% during model loading.

**Root Cause:** Memory fragmentation - Windows can't allocate large contiguous blocks.

**Solution:**
- Restart computer (clears fragmentation)
- Close other applications
- Use compatible version (float16) instead of 4-bit
- Check available RAM before loading

**Prevention:**
- Restart before loading model
- Close unnecessary applications
- Use compatible version on Windows CPU

---

### 2. Total Count Shows 20

**Problem:** Total count always shows 20 (top_k limit) instead of true database counts.

**Root Cause:** COUNT query didn't apply similarity threshold.

**Solution:**
- Added similarity threshold to COUNT query
- Filtered queries: No threshold (exact count)
- Semantic queries: Apply threshold (estimated count)

**Note:** Semantic search counts may differ from exact SQL LIKE counts (expected behavior).

---

### 3. Lookup Tables Not Used

**Problem:** Embeddings include IDs (e.g., "Type: 4") instead of descriptive names (e.g., "Type: תכנון").

**Root Cause:** Database stores IDs, descriptive values in separate lookup tables.

**Solution:**
- Create lookup mapping file (`config/lookup_mappings.json`)
- Update text processing to include both ID and name
- Auto-detection system for future projects

**Status:** Solution designed, ready for implementation

---

### 4. 4-bit Quantization Hangs on Windows CPU

**Problem:** 4-bit quantization hangs after loading shards on Windows CPU.

**Root Cause:** Known limitation of bitsandbytes on Windows CPU.

**Solution:**
- Use compatible version (float16) on Windows CPU
- Use high-end version (4-bit) on servers/Linux
- Automatic detection in compatible version

---

### 5. Cursor/VSCode Timeouts

**Problem:** Terminal resets or shows "Serialization error" during long operations.

**Root Cause:** Cursor/VSCode internal timeout, not a code error.

**Solution:**
- Run tests in separate PowerShell terminal outside Cursor
- Use standalone test scripts
- Pre-load model in test scripts

---

## Best Practices

### 1. Always Test After Changes

**Before making changes:**
- Understand what you're changing
- Test with real queries
- Compare before/after results

**After making changes:**
- Run test queries
- Verify results are correct
- Check for regressions

---

### 2. Regenerate Embeddings After Field Changes

**When to regenerate:**
- After changing field weights
- After adding/removing fields
- After implementing lookup tables
- After changing chunk size/overlap

**How to regenerate:**
```bash
python scripts/core/generate_embeddings.py
```

**Time:** ~1-2 hours for 8,195 requests

---

### 3. Use Appropriate Search Type

**Type 1 (Search Only):**
- Use for fast exploration
- When you just need a list
- When you don't need text answer

**Type 3 (Full RAG):**
- Use for questions ("how many?", "what?")
- When you want text answer
- When you're okay waiting first time

---

### 4. Monitor Memory Usage

**Before loading LLM:**
- Check available RAM
- Close unnecessary applications
- Restart if needed (clears fragmentation)

**During operation:**
- Monitor RAM usage
- Watch for memory errors
- Restart if issues occur

---

### 5. Document Changes

**When making changes:**
- Document what you changed
- Document why you changed it
- Update relevant documentation
- Note any side effects

---

## Important Limitations

### 1. Memory Fragmentation

**Issue:** Windows can't allocate large contiguous blocks for model loading.

**Impact:** Model loading may fail even with sufficient RAM.

**Workaround:**
- Restart computer before loading
- Use compatible version (float16)
- Close other applications

**Future:** Consider using Linux for production servers.

---

### 2. 4-bit Quantization on Windows CPU

**Issue:** Hangs after loading shards on Windows CPU.

**Impact:** Can't use 4GB model on Windows CPU.

**Workaround:**
- Use compatible version (float16, 7-8GB)
- Use high-end version on Linux/servers
- Automatic detection in compatible version

---

### 3. Semantic Search Counts

**Issue:** Semantic search counts differ from exact SQL LIKE counts.

**Impact:** Total count may be different from expected.

**Why:** Semantic search is more flexible, finds similar meanings.

**This is expected behavior** for semantic search systems.

---

### 4. Model Loading Time

**Issue:** First RAG query takes 2-5 minutes (model loading).

**Impact:** Slow first query, fast subsequent queries.

**Workaround:**
- Pre-load model if needed
- Use search-only for fast results
- Model stays in memory after loading

---

### 5. Python Version Compatibility

**Issue:** bitsandbytes doesn't work on Python 3.14+.

**Impact:** Can't use 4-bit quantization on Python 3.14+.

**Solution:**
- Use Python 3.13 or earlier for 4-bit
- Use Python 3.13+ with float16 fallback
- Automatic detection in code

---

## What to Know Before Making Changes

### 1. Understand the Flow

**Before changing anything:**
- Understand how data flows through the system
- Know which components interact
- Understand dependencies

**Read:**
- `06_SYSTEM_FLOW_AND_ARCHITECTURE.md` - Overall flow
- Component-specific docs (01-05)
- Code comments

---

### 2. Test Incrementally

**When making changes:**
- Make small changes
- Test after each change
- Verify results are correct
- Don't change multiple things at once

---

### 3. Backup Before Major Changes

**Before regenerating embeddings:**
- Backup database
- Backup configuration files
- Document current state

**Before changing field weights:**
- Note current weights
- Test impact of changes
- Can revert if needed

---

### 4. Understand Dependencies

**Component dependencies:**
- RAG depends on search
- Search depends on embeddings
- Embeddings depend on field weighting
- Query parser affects search and RAG

**Changing one component may affect others!**

---

### 5. Know the Configuration

**Before changing parameters:**
- Understand what the parameter does
- Know current value
- Understand impact of change
- Test with real queries

**Read:**
- `08_CONFIGURATION_AND_TUNING.md` - All parameters
- `CONFIGURABLE_PARAMETERS_GUIDE.md` - Detailed guide

---

## Summary

**Key Concepts:**
- Two models (embedding for search, LLM for answers)
- Semantic search vs exact match
- Field weighting emphasizes important fields
- Chunking handles long text
- Similarity thresholds filter noise

**Common Gotchas:**
- Model loading crashes (memory fragmentation)
- Total count shows 20 (needs threshold)
- Lookup tables not used (IDs vs names)
- 4-bit quantization hangs on Windows CPU
- Cursor/VSCode timeouts

**Best Practices:**
- Always test after changes
- Regenerate embeddings after field changes
- Use appropriate search type
- Monitor memory usage
- Document changes

**Important Limitations:**
- Memory fragmentation on Windows
- 4-bit quantization on Windows CPU
- Semantic search counts differ from exact counts
- Model loading time (first query slow)
- Python version compatibility

**Before Making Changes:**
- Understand the flow
- Test incrementally
- Backup before major changes
- Understand dependencies
- Know the configuration

---

**Last Updated:** Current Session  
**Status:** Complete knowledge base

