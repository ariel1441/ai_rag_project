# RAG Troubleshooting Guide

## Common Issues

### Issue 1: Model Loading Takes Too Long or Crashes

**Symptoms:**
- Loading checkpoint shards stuck at 33%
- Process appears frozen
- Out of memory errors

**Causes:**
- Loading 15GB model into RAM
- Not enough free RAM
- CPU loading is slow

**Solutions:**

1. **Check Available RAM:**
   ```bash
   python scripts/helpers/check_system_ram.py
   ```
   - Need: ~16GB free RAM
   - If less, close other applications

2. **Use Quantized Model (Alternative):**
   - Download 4GB quantized version instead
   - Much faster loading
   - Slightly lower quality (95-98%)

3. **Wait Longer:**
   - First load: 1-2 minutes on CPU
   - Subsequent queries: Faster (model stays in memory)

4. **Check if Process is Still Running:**
   - Look for progress in terminal
   - Check Task Manager for Python process
   - If stuck > 5 minutes, might be an issue

---

### Issue 2: Out of Memory Error

**Error:** `RuntimeError: CUDA out of memory` or `MemoryError`

**Solutions:**

1. **Close Other Applications:**
   - Free up RAM
   - Need ~16GB free

2. **Use Quantized Model:**
   - 4GB instead of 15GB
   - Still excellent quality

3. **Reduce Batch Size:**
   - Not applicable for single queries
   - But can help if processing multiple

---

### Issue 3: Model Not Found

**Error:** `FileNotFoundError: Model not found`

**Solutions:**

1. **Check Model Path:**
   ```bash
   python scripts/helpers/check_download_status.py
   ```

2. **Verify Download:**
   - Should be in: `D:\ai_learning\train_ai_tamar_request\models\llm\mistral-7b-instruct`
   - Should have 3 `.safetensors` files

3. **Re-download if Needed:**
   ```bash
   python scripts/core/download_rag_model.py
   ```

---

### Issue 4: Slow Generation

**Symptom:** Takes 30+ seconds per answer

**Causes:**
- CPU inference (no GPU)
- Large model (15GB)
- First query (model loading)

**Solutions:**

1. **First Query is Slow:**
   - Normal: 30-60 seconds (loading model)
   - Subsequent queries: 5-15 seconds

2. **Use GPU (if available):**
   - Much faster (1-3 seconds)
   - Automatic if GPU detected

3. **Use Quantized Model:**
   - Faster loading
   - Slightly faster inference

---

### Issue 5: Wrong Answers

**Symptom:** RAG gives incorrect answers

**Possible Causes:**

1. **Poor Retrieval:**
   - Search not finding right requests
   - **Fix:** Improve search (check embeddings, boosting)

2. **Poor Prompts:**
   - LLM not understanding context
   - **Fix:** Improve prompt templates

3. **Wrong Context:**
   - Retrieved requests not relevant
   - **Fix:** Improve search logic

**Debugging:**

1. **Check Retrieved Requests:**
   - RAG shows "BASED ON X RELEVANT REQUESTS"
   - Verify these are correct

2. **Check Search:**
   - Test search separately: `python scripts/core/search.py`
   - Verify search results are good

3. **Check Prompts:**
   - Add debug output to see prompt
   - Verify context is formatted correctly

---

### Issue 6: Hebrew Display Issues

**Symptom:** Hebrew text displays incorrectly

**Solutions:**

1. **RTL Fix Applied:**
   - Should be automatic
   - Check `fix_hebrew_rtl()` is called

2. **Terminal Encoding:**
   - Run: `chcp 65001` in terminal
   - Or use Windows Terminal

---

## Performance Tips

### For Faster Loading:

1. **Keep Model in Memory:**
   - Don't close RAG script between queries
   - Model stays loaded

2. **Use GPU:**
   - Much faster if available
   - Automatic detection

3. **Reduce Model Size:**
   - Use quantized (4GB) instead of full (15GB)
   - Faster loading, still good quality

### For Better Answers:

1. **Improve Search:**
   - Better embeddings
   - Better query parsing
   - Better boosting

2. **Improve Prompts:**
   - Add examples
   - Better instructions
   - Format constraints

3. **More Context:**
   - Increase `top_k` (default: 20)
   - More requests = better context

---

## Quick Fixes

### If Model Won't Load:

```python
# Try loading with less memory
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16,  # Half precision
    low_cpu_mem_usage=True
)
```

### If Generation is Too Slow:

```python
# Reduce max tokens
outputs = model.generate(
    **inputs,
    max_new_tokens=200,  # Instead of 500
    ...
)
```

### If Answers are Wrong:

1. Check search results first
2. Verify embeddings are good
3. Improve prompt templates
4. Add more context

---

## Getting Help

If issues persist:

1. **Check Logs:**
   - Look for error messages
   - Check terminal output

2. **Verify Setup:**
   - Model downloaded correctly
   - Enough RAM
   - Dependencies installed

3. **Test Components:**
   - Test search: `python scripts/core/search.py`
   - Test parser: `python scripts/tests/test_query_parser.py`
   - Test embeddings: `python scripts/tests/test_embeddings_quality.py`

---

## Status Check Commands

```bash
# Check RAM
python scripts/helpers/check_system_ram.py

# Check model download
python scripts/helpers/check_download_status.py

# Test search
python scripts/core/search.py

# Test RAG
python scripts/core/rag_query.py
```

