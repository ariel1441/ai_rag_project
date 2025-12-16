# 🚀 Prompt for New Chat Session

**Copy and paste this entire prompt when starting a new chat session:**

---

## 📋 Context & Instructions

I'm working on a **Retrieval-Augmented Generation (RAG) system** for querying a database of requests/actions/transactions in Hebrew. The project has been through significant development and was recently migrated to a new PC with GPU support.

**Your task:** Understand the entire project by reading all documentation and code systematically. I need you to fully comprehend:

1. **The main core original logic** - How the system fundamentally works
2. **What improvements were made** - All enhancements and fixes
3. **What's planned** - Future features and roadmap
4. **Testing results** - What was tested and what was found
5. **Current goal** - Testing RAG on a better PC with GPU

---

## 📚 Required Reading (In This Order)

### Phase 1: Start Here - Project Overview
**Read FIRST:**
- `docs/NEW_CHAT_START_HERE.md` - **START HERE!** Complete overview, migration summary, system architecture

### Phase 2: Core System Understanding
**Read to understand the original logic:**
- `docs/HOW_SEARCH_AND_RAG_WORK.md` - Explains search vs RAG, how they work
- `docs/SEARCH_IMPROVEMENTS_COMPLETE_SUMMARY.md` - **CRITICAL** - Complete search logic explanation (3-layer hybrid search)
- `docs/UNDERSTANDING_EMBEDDINGS_AND_RAG.md` - Core concepts of embeddings and RAG
- `README.md` - Project structure and quick start

### Phase 3: Improvements & Fixes
**Read to understand what was improved:**
- `docs/ALL_FIXES_SUMMARY.md` - Summary of all fixes (emphasizes generic nature)
- `docs/ALL_CHANGES_SUMMARY.md` - All changes made to the system
- `docs/IMPROVEMENTS_IMPLEMENTED.md` - Detailed improvements
- `docs/SEARCH_LOGIC_DEEP_DIVE.md` - Deep dive into search architecture
- `docs/AND_LOGIC_IMPLEMENTATION.md` - AND logic for multi-entity queries

### Phase 4: Testing & Results
**Read to understand testing:**
- `docs/FINAL_TEST_SUMMARY_FOR_USER.md` - User-friendly test summary
- `docs/COMPREHENSIVE_TEST_ANALYSIS_AND_FIXES.md` - Detailed test analysis
- `docs/TESTING_SUMMARY_AND_LOGIC.md` - Testing summary for AND logic
- `docs/FINAL_IMPLEMENTATION_STATUS.md` - Final implementation status

### Phase 5: Migration & Current State
**Read to understand recent migration:**
- `docs/TRANSFER_TO_NEW_PC_GUIDE.md` - Complete transfer guide
- `docs/START_RAG_SERVER_AND_TEST.md` - How to start and test RAG
- `docs/GPU_SETUP_AND_DATABASE_GUIDE.md` - GPU setup and database guide

### Phase 6: Future Plans
**Read to understand what's planned:**
- `docs/FEATURE_IDEAS_AND_ROADMAP.md` - Feature ideas and roadmap
- `docs/RAG_SYSTEM_POTENTIAL_AND_CAPABILITIES.md` - Future capabilities
- `docs/FEATURE_IMPLEMENTATION_GUIDES.md` - Implementation guides

### Phase 7: Generic/Universal Components
**Read to understand generic setup:**
- `docs/GENERIC_EMBEDDING_COMPLETE_GUIDE.md` - Generic embedding setup
- `docs/EMBEDDING_SETUP_GUIDE.md` - Embedding setup guide
- `docs/GENERIC_EMBEDDING_FULL_PROCESS_EXPLANATION.md` - Full process explanation

### Phase 8: Feature Documentation
**Read to understand implemented features:**
- `docs/QUERY_HISTORY_FEATURE_SUMMARY.md` - Query history feature
- `docs/QUERY_HISTORY_STORAGE_EXPLANATION.md` - How query history works

---

## 🔍 Key Code Files to Review

After reading documentation, review these critical code files:

### Core System:
- `scripts/core/rag_query.py` - Base RAG system (CPU-optimized)
- `scripts/core/rag_query_gpu.py` - GPU-optimized RAG system
- `scripts/core/generate_embeddings.py` - Embedding generation
- `api/services.py` - SearchService and RAGService
- `api/app.py` - FastAPI endpoints

### Utilities:
- `scripts/utils/query_parser.py` - Query parsing and intent detection
- `scripts/utils/text_processing.py` - Text combination and chunking
- `config/search_config.json` - Query patterns and configurations

### Test Scripts:
- `scripts/tests/test_rag_comprehensive.py` - Comprehensive RAG tests
- `scripts/tests/test_embedding_chunk_count.py` - Embedding verification

---

## 🎯 What You Need to Understand

### 1. Main Core Original Logic

**The system works in 3 layers:**

1. **Query Parsing** (`query_parser.py`)
   - Detects intent: person, project, type, status, general
   - Extracts entities: names, IDs, dates, urgency
   - Determines query type: find, count, summarize, similar, urgent

2. **Hybrid Search** (`services.py`)
   - **Layer 1:** SQL filters (exact matches: type_id, status_id, dates)
   - **Layer 2:** Text filters (LIKE patterns for person/project names)
   - **Layer 3:** Semantic ranking (vector similarity with field-specific boosting)
   - Returns top-K relevant requests

3. **RAG Generation** (`rag_query.py` / `rag_query_gpu.py`)
   - Retrieves relevant requests
   - Formats context for LLM
   - Generates natural language answer using Mistral-7B
   - Returns answer + list of requests

**Key Points:**
- Embeddings stored in `request_embeddings` table (40k chunks)
- Field weighting: 3.0x (critical), 2.0x (important), 1.0x (supporting), 0.5x (booleans/coordinates)
- Text chunking: 512 chars, 50 overlap
- Database: PostgreSQL with pgvector extension

### 2. What We Did to Improve

**Search Improvements:**
- ✅ AND logic for multiple entities (person + type, person + status, etc.)
- ✅ Field-specific boosting (exact matches get 2.0x boost)
- ✅ Similar requests by request ID
- ✅ Date and urgency filtering
- ✅ Project counting
- ✅ Answer retrieval from similar requests
- ✅ Robust query parsing (handles Hebrew patterns, edge cases)

**System Improvements:**
- ✅ GPU optimization (automatic detection, faster inference)
- ✅ Query history feature (modular, easily removable)
- ✅ Enhanced field matching (handles BOM, case variations)
- ✅ Comprehensive test suite
- ✅ Generic embedding setup for new clients

**All fixes are generic and logic-based, NOT hard-coded!**

### 3. What We Plan to Do

**Future Features (from roadmap):**
- Advanced Filters UI
- Dashboard & Analytics
- Auto-response generation
- Prediction capabilities (approval/rejection)
- Trend forecasting

**Current Focus:**
- Testing RAG on better PC with GPU
- Verifying all query types work correctly
- Performance optimization

### 4. Testing Results

**What Was Tested:**
- ✅ Search accuracy (comprehensive test suite)
- ✅ Query parsing (all query types)
- ✅ AND logic (multi-entity queries)
- ✅ Embedding generation (verified ~40k chunks)
- ✅ RAG answer quality

**Key Findings:**
- Search accuracy: 85-95% for most query types
- AND logic works correctly (filters properly combined)
- Embedding logic produces correct chunk count (~40k)
- GPU provides 3-10x speedup vs CPU
- Field matching robust (handles CSV import variations)

**Issues Found & Fixed:**
- Person name extraction improved (handles "מ" prefix, stops at type/status patterns)
- Query type detection improved (less false positives)
- Count accuracy fixed (SQL filters + similarity threshold)
- Field matching enhanced (BOM, case, naming variations)

### 5. Current Goal - Testing RAG on Better PC

**What's Done:**
- ✅ Project transferred to new PC via Git
- ✅ Database set up with Docker (pgvector on port 5433)
- ✅ Data imported (8,195 requests)
- ✅ Embeddings imported (40k chunks)
- ✅ GPU-optimized RAG system enabled
- ✅ Test scripts created

**What's Next:**
- Run comprehensive RAG tests (`test_rag_comprehensive.py`)
- Test all query types manually via web interface
- Verify GPU is being used
- Check answer quality and speed
- Document any issues or improvements needed

**Current Status:**
- System is operational
- GPU detection working
- Ready for comprehensive testing

---

## ⚠️ Important Principles

1. **Generic Code:** All fixes are generic and logic-based, NOT hard-coded for specific cases
2. **Modular Features:** New features (like query history) are modular and easily removable
3. **Backward Compatibility:** Changes don't break existing functionality
4. **Testing First:** Always test changes before committing
5. **Documentation:** Keep documentation updated when making changes

---

## 🔧 Current Environment

- **Database:** Docker PostgreSQL on port 5433
- **API:** FastAPI on port 8000
- **GPU:** Available and being used (automatic detection)
- **Models:** Auto-downloaded (not in Git)
- **Embeddings:** 40k chunks in `request_embeddings` table
- **Data:** 8,195 requests in `requests` table

---

## 📝 After Reading Everything

Once you've read all the documentation and reviewed the code:

1. **Confirm understanding** of:
   - The 3-layer hybrid search architecture
   - How RAG works (retrieval + generation)
   - What improvements were made and why
   - Current testing goals

2. **Ask clarifying questions** if anything is unclear

3. **Be ready to:**
   - Help test RAG queries
   - Debug any issues found
   - Suggest improvements
   - Continue development

---

## 🚀 Quick Start Commands

**Start API Server:**
```powershell
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

**Run RAG Tests:**
```powershell
python scripts/tests/test_rag_comprehensive.py
```

**Verify Embeddings:**
```powershell
python scripts/tests/test_embedding_chunk_count.py
```

---

**Remember:** The system is working well. Be careful not to break existing functionality when making changes. All improvements should be generic and well-tested.

**Now please read all the documentation files listed above, review the key code files, and confirm your understanding of the system before proceeding with any tasks.**

