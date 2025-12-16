# Action Plan: Next Steps

## 🔍 Issue: Files Disappearing

**Problem**: `MENTOR_GUIDE.md` (and possibly other files) disappeared after Cursor restart.

**Why this happens**:
- Files might not have been saved before closing
- Cursor doesn't auto-save by default
- Some files might be in `.gitignore` (but `.md` files aren't)

**Solution**:
1. ✅ Always save files before closing Cursor (Ctrl+S or Cmd+S)
2. ✅ Enable auto-save in Cursor settings
3. ✅ Check `.gitignore` to ensure important files aren't excluded
4. ✅ Use Git to track important files (if using version control)

**Current Status**: `.gitignore` looks good - it doesn't exclude `.md` files. The file might not have been saved.

---

## 📋 Current Project Status

### ✅ What's Done:
1. **Database Setup**: PostgreSQL + pgvector working
2. **Data Import**: 1,175 requests imported
3. **Embeddings**: 1,237 embeddings generated (but only 8 fields used)
4. **Search**: Semantic + hybrid search working
5. **Hebrew Support**: RTL display fix implemented

### ⚠️ What Needs Improvement:
1. **Embeddings**: Only 8 of 83 fields included
2. **RAG**: Not yet implemented (can't answer questions)

### 🎯 What's Next:
1. **Improve Embeddings** (Priority 1)
2. **Build RAG Pipeline** (Priority 2)
3. **Test with New Table** (After RAG is done)

---

## 🎯 Step 1: Improve Embeddings (NEXT TASK)

### Problem:
- Only 8 fields included: `projectname`, `projectdesc`, `areadesc`, `remarks`, `requestjobshortdescription`, `requeststatusid`, `requesttypeid`
- Missing important fields: `updatedby`, `createdby`, `responsibleemployeename`, `contactfirstname`, `contactlastname`, `metahnen_contactname`, `kabalan_contactname`, `yazam_contactname`
- This causes search to miss results (e.g., "פניות מאריאל בן עקיבא" doesn't find requests where `updatedby = 'אריאל בן עקיבא'`)

### Solution: Field Weighting System

**Approach**:
1. **Categorize all 83 fields** by importance:
   - **Critical** (weight: 3x, repeat 2-3 times): Project name, description, area, remarks
   - **Important** (weight: 2x, repeat 1-2 times): Status, type, responsible employee, contacts, names
   - **Supporting** (weight: 1x): Dates, IDs, metadata, company names
   - **Low Priority** (weight: 0.5x): Coordinates, flags, technical fields

2. **Update `combine_text_fields()`** to include:
   - All text fields (names, descriptions, etc.)
   - Field-specific formatting (e.g., "Updated by: {updatedby}")
   - Weighting (repeat important fields)
   - Smart handling of empty/null values

3. **Regenerate embeddings** for all requests

### Implementation Steps:

1. **Update `scripts/generate_embeddings_from_db.py`**:
   - Rewrite `combine_text_fields()` with field weighting
   - Add all relevant fields
   - Test with a few requests first

2. **Clear old embeddings** (optional, or just regenerate):
   ```sql
   TRUNCATE TABLE request_embeddings;
   ```

3. **Regenerate embeddings**:
   ```bash
   python scripts/generate_embeddings_from_db.py
   ```

4. **Test search**:
   ```bash
   python scripts/search.py
   ```
   - Test query: "פניות מאריאל בן עקיבא"
   - Should now find requests where `updatedby` or `createdby` contains "אריאל"

### Expected Result:
- ✅ Search finds requests by contact names
- ✅ Search finds requests by responsible employees
- ✅ Search finds requests by creator/updater names
- ✅ Better overall search relevance

### Time Estimate: 2-4 hours
- Update function: 1 hour
- Regenerate embeddings: 1-2 hours (for 1,175 requests)
- Testing: 1 hour

---

## 🚀 Step 2: Build RAG Pipeline (AFTER EMBEDDINGS)

### Problem:
- Current system only returns list of requests
- Can't answer questions like "How many requests are about אלינור?"
- Can't summarize or analyze patterns

### Solution: RAG (Retrieval-Augmented Generation)

**Components**:
1. **LLM Model**: Mistral-7B-v0.1 (recommended)
   - License: Apache 2.0 (commercial OK)
   - Size: ~14GB
   - VRAM: 8GB (8-bit quantization)
   - Download: One-time from HuggingFace

2. **RAG Pipeline**:
   - Use existing search to find relevant requests
   - Retrieve top-K requests (e.g., top 20)
   - Assemble prompt with context + query
   - Send to LLM for answer generation
   - Return natural language answer

### Implementation Steps:

1. **Choose and Download LLM**:
   - Model: `mistralai/Mistral-7B-v0.1`
   - Will download automatically on first use (~14GB, 30-60 minutes)

2. **Create `scripts/rag_query.py`**:
   ```python
   # Pseudo-code:
   def rag_query(query):
       # 1. Use existing search to find relevant requests
       results = search_embeddings(query, top_k=20)
       
       # 2. Retrieve full request data
       context = get_requests_from_db(results)
       
       # 3. Assemble prompt
       prompt = f"""Based on these requests:
       {context}
       
       Question: {query}
       
       Answer:"""
       
       # 4. Load LLM (if not already loaded)
       if llm_model is None:
           llm_model = load_mistral_7b()
       
       # 5. Generate answer
       answer = llm_model.generate(prompt)
       
       # 6. Return answer
       return answer
   ```

3. **Test RAG**:
   - Test with Hebrew queries
   - Test with different question types:
     - Count: "How many requests are about אלינור?"
     - Summarize: "Summarize requests from last month"
     - Analyze: "What are the most common request types?"

### Expected Result:
- ✅ System answers questions directly (not just returns lists)
- ✅ Can count, summarize, and analyze
- ✅ Works with Hebrew queries
- ✅ Answers based on actual data (no hallucination)

### Time Estimate: 4-8 hours
- Download LLM: 30-60 minutes (one-time)
- Build RAG pipeline: 2-3 hours
- Testing: 2-4 hours

---

## 🧪 Step 3: Test with New Table (AFTER RAG)

### When to Do This:
- After embeddings are improved
- After RAG is working
- When you have the new table ready

### Process:
1. **Export new table** from SQL Server (same process as before)
2. **Import to PostgreSQL** (create new table or append to existing)
3. **Generate embeddings** for new data
4. **Test search** with new data
5. **Test RAG** with new data
6. **Compare results** with old table

### Benefits:
- Validates system works with larger datasets
- Tests scalability
- Identifies any issues before production

### Time Estimate: 4-6 hours
- Export/Import: 1-2 hours
- Generate embeddings: 1-3 hours (depends on size)
- Testing: 1-2 hours

---

## 📊 Complete Roadmap

### Phase 1: Improve Embeddings (NOW)
- [ ] Update `combine_text_fields()` with field weighting
- [ ] Add all relevant fields (names, contacts, etc.)
- [ ] Test with sample requests
- [ ] Regenerate all embeddings
- [ ] Test search with improved embeddings
- [ ] Verify "פניות מאריאל בן עקיבא" now works

**Time**: 2-4 hours  
**Priority**: HIGH (affects search quality)

---

### Phase 2: Build RAG Pipeline (NEXT)
- [ ] Choose LLM model (Mistral-7B recommended)
- [ ] Download LLM (one-time, 30-60 min)
- [ ] Create `scripts/rag_query.py`
- [ ] Integrate with existing search
- [ ] Test with Hebrew queries
- [ ] Test different question types
- [ ] Optimize prompt templates

**Time**: 4-8 hours  
**Priority**: HIGH (enables question-answering)

---

### Phase 3: Test with New Table (AFTER RAG)
- [ ] Export new table from SQL Server
- [ ] Import to PostgreSQL
- [ ] Generate embeddings for new data
- [ ] Test search with new data
- [ ] Test RAG with new data
- [ ] Compare results

**Time**: 4-6 hours  
**Priority**: MEDIUM (validation)

---

### Phase 4: Future Enhancements (OPTIONAL)
- [ ] Field-specific query parsing ("projectname אלינור")
- [ ] Hebrew field name mapping ("מסוג" → `requesttypeid`)
- [ ] Multi-condition queries (AND/OR logic)
- [ ] Fine-tuning (if RAG quality needs improvement)
- [ ] API integration (FastAPI)
- [ ] Web interface

**Time**: TBD  
**Priority**: LOW (nice-to-have)

---

## 🎯 Recommended Order

1. **NOW**: Improve Embeddings (Step 1)
   - Fixes search quality issues
   - Makes RAG work better (better context retrieval)
   - Quick win (2-4 hours)

2. **NEXT**: Build RAG Pipeline (Step 2)
   - Enables question-answering
   - Main feature users want
   - Builds on improved embeddings

3. **LATER**: Test with New Table (Step 3)
   - Validates system
   - Tests scalability
   - After core features work

---

## 💡 Quick Start: Improve Embeddings

**Ready to start?** Here's what we'll do:

1. **Update `combine_text_fields()`** in `scripts/generate_embeddings_from_db.py`
2. **Add all relevant fields** with proper weighting
3. **Test with a few requests** first
4. **Regenerate all embeddings**
5. **Test search** to verify improvement

**Should I start implementing the improved `combine_text_fields()` function now?**

---

*Last Updated: Current project state*  
*Next Action: Improve embeddings with field weighting*

