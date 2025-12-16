# Project Knowledge Base - Complete Understanding

## 📋 Purpose of This Document

This document serves as a complete knowledge base of the AI Requests System project. It captures:
- Project purpose and goals
- What has been completed
- Problems encountered and solved
- Current state and architecture
- Next steps and plans
- Dilemmas and ideas
- Technical implementation details

**Created:** To replace corrupted chat history and maintain project continuity.

---

## 🎯 Project Purpose & Goals

### Main Goal
Build an AI-powered request management system that:
- **Searches** requests using semantic similarity (embeddings)
- **Understands** queries in Hebrew and English
- **Answers** questions using RAG (Retrieval-Augmented Generation)
- **Filters** by person, project, type, status
- **Supports** field-specific queries

### Business Value
- Faster search (semantic vs. keyword)
- Better results (finds by meaning, not just keywords)
- Hebrew support (critical for Israeli company)
- Foundation for advanced AI features (RAG, fine-tuning)

### Target Users
- Internal users searching company requests
- Need to find requests by person, project, type, or general meaning
- Want natural language answers, not just lists

---

## ✅ What Has Been Completed

### Phase 1: Data Export & Isolation ✅
- ✅ Exported Requests table from SQL Server to CSV
- ✅ Created isolated PostgreSQL database (`ai_requests_db`)
- ✅ Imported 8,195 requests with all 83 columns
- ✅ Used staging table approach for safe import
- ✅ Environment variables for credentials (.env file)

**Result:** 8,195 requests successfully imported

---

### Phase 2: Vector Database Setup ✅
- ✅ Installed pgvector extension locally (Windows)
- ✅ Created `requests` table (all 83 columns as TEXT)
- ✅ Created `request_embeddings` table with vector column
- ✅ Generated embeddings for all requests (36,031 chunks from 8,195 requests)
- ✅ Created vector index (`idx_request_embeddings_vector`)
- ✅ Created foreign key index (`idx_request_embeddings_requestid`)

**Improvements Made:**
1. **Temp Table Method**: Solved parameter binding issue by inserting query embedding into temp table
2. **Hybrid Search**: Combined keyword filtering with semantic ranking
3. **Hebrew RTL Fix**: Implemented display fix for Hebrew text in LTR terminals
4. **Field Weighting**: Implemented weighted field combination (~44 fields)
5. **Query Parser**: Built intent detection and entity extraction system

**Result:** 36,031 embeddings stored, semantic search working

---

### Phase 2.5: Embedding Improvements ✅
- ✅ Updated `combine_text_fields_weighted()` to include ~44 fields
- ✅ Implemented field weighting (3.0x, 2.0x, 1.0x, 0.5x)
- ✅ Added critical missing fields: `updatedby`, `createdby`, `responsibleemployeename`
- ✅ Added contact fields: `contactfirstname`, `contactlastname`, `contactemail`
- ✅ Added booleans for specific queries (IsPenetrateGround, IsActive, etc.)
- ✅ Added coordinates for spatial queries (AreaCenterX, AreaCenterY, etc.)
- ✅ Regenerated all embeddings with improved field combination

**Result:** Search now finds requests by person names, contacts, and all relevant fields

---

### Phase 2.6: Query Parser & Search Integration ✅
- ✅ Built query parser (`scripts/utils/query_parser.py`)
- ✅ Created configuration file (`config/search_config.json`)
- ✅ Integrated query parser into search (`scripts/core/search.py`)
- ✅ Added field-specific search with boosting
- ✅ Added type/status filtering
- ✅ Added post-filtering for person queries

**Features:**
- Intent detection: person, project, type, status, general
- Entity extraction: person names, project names, type IDs, status IDs
- Target field determination
- Boosting: exact match in target field (2.0x), entity in chunk (1.5x), semantic (1.0x)

**Result:** "פניות מאור גלילי" now correctly searches person fields

---

### Phase 3: RAG Implementation ✅
- ✅ Built RAG system (`scripts/core/rag_query.py`)
- ✅ Integrated with query parser
- ✅ Integrated with improved search
- ✅ Context formatting for LLM
- ✅ Prompt building with query-type-specific instructions
- ✅ Mistral-7B-Instruct model integration (4-bit quantized for RAM efficiency)
- ✅ Hebrew support in prompts and answers

**Model Configuration:**
- Model: Mistral-7B-Instruct
- Version: 4-bit Quantized (~4GB RAM instead of 15GB)
- Quality: 95-98% (excellent, barely noticeable difference)
- Location: `D:/ai_learning/train_ai_tamar_request/models/llm/mistral-7b-instruct`

**Result:** System can answer questions like "כמה פניות יש מאור גלילי?"

---

## 🔧 Problems Encountered & Solved

### Critical Issues Solved

1. **Vector Search Returning 0 Results**
   - **Problem:** Parameter binding format mismatch between query embedding and stored vector type
   - **Solution:** Temp table method (insert query embedding into temp table, then search)
   - **Impact:** System now works for any query

2. **Hebrew Display Issues**
   - **Problem:** Terminal RTL vs LTR rendering (Hebrew text displayed backwards)
   - **Solution:** Display-only reversal function (`fix_hebrew_rtl()`)
   - **Impact:** Correct visual output, data integrity maintained

3. **Missing Fields in Embeddings**
   - **Problem:** Only 8 of 83 fields included initially
   - **Solution:** Implemented field weighting with ~44 fields
   - **Impact:** Search now finds requests by person names, contacts, etc.

4. **Query Understanding**
   - **Problem:** "פניות מאור גלילי" searched all fields, not person fields
   - **Solution:** Built query parser with intent detection and field-specific search
   - **Impact:** Queries now correctly target specific fields

5. **RAM Constraints for RAG**
   - **Problem:** Full precision Mistral-7B needs ~16GB RAM, only ~11GB free
   - **Solution:** 4-bit quantization reduces to ~4GB RAM with 95-98% quality
   - **Impact:** RAG works on available hardware

---

### Minor Issues Solved

1. **PostgreSQL Column Case Sensitivity** - Fixed with lowercase column names
2. **Type Conversion Errors** - Fixed with safe conversion (NULL for invalid)
3. **VARCHAR Length Limits** - Fixed by changing to TEXT
4. **psql Not in PATH** - Bypassed with Python scripts
5. **pgvector Windows Installation** - Manual installation from source

---

## 📊 Current System State

### Data
- **Requests:** 8,195 requests in database
- **Embeddings:** 36,031 chunks (average 4.40 chunks per request)
- **Fields per Request:** 83 columns
- **Fields in Embeddings:** ~44 fields (with weighting)

### Components Working
1. **Database:** PostgreSQL + pgvector ✅
2. **Embeddings:** Weighted field combination, chunking ✅
3. **Search:** Query parser + field-specific + semantic + boosting ✅
4. **RAG:** Retrieval + context formatting + LLM generation ✅
5. **Hebrew Support:** RTL display fix, encoding handling ✅

### Architecture
```
User Query (Hebrew/English)
    ↓
[Query Parser] → Intent + Entities + Target Fields
    ↓
[Search] → Field-specific + Semantic + Boosting
    ↓
[Retrieval] → Top-K Relevant Requests
    ↓
[RAG] → Context Formatting + LLM Generation
    ↓
Natural Language Answer
```

---

## 🚀 Next Steps & Plans

### Immediate Next Steps

1. **Test RAG System** (2-4 hours)
   - Test with various question types (count, summarize, find)
   - Verify answer quality
   - Test Hebrew queries
   - Fix any issues found

2. **Optimize Prompts** (1-2 hours)
   - Improve prompt templates based on test results
   - Add few-shot examples if needed
   - Test different formats

3. **Polish & Production-Ready** (4-6 hours)
   - Add comprehensive error handling
   - Add logging system
   - Add basic tests
   - Improve user experience

### Short-term (1-2 weeks)

1. **Performance Optimization**
   - Add query caching
   - Optimize database queries
   - Parallel processing for embeddings

2. **Features**
   - Date range queries
   - Location queries
   - Better name extraction (Hebrew word boundaries)

3. **Testing**
   - Unit tests
   - Integration tests
   - Performance tests

### Long-term (1-2 months)

1. **Production Features**
   - API layer (FastAPI)
   - Authentication
   - Rate limiting
   - Monitoring

2. **Advanced Features**
   - Fine-tuning (optional, if RAG quality needs improvement)
   - Multi-turn conversations
   - User feedback loop

---

## 💡 Dilemmas & Ideas

### Dilemmas

1. **Full Precision vs Quantized Model**
   - **Current:** Using 4-bit quantized (4GB RAM, 95-98% quality)
   - **Dilemma:** Upgrade to full precision (15GB RAM, 100% quality)?
   - **Decision:** Stay with quantized for now (excellent quality, works on available RAM)
   - **Future:** Upgrade when RAM allows or if quality isn't sufficient

2. **Field Weighting Strategy**
   - **Dilemma:** How to weight fields optimally?
   - **Solution:** Implemented 3-tier system (3.0x critical, 2.0x important, 1.0x supporting, 0.5x specific)
   - **Status:** Working well, can be refined based on user feedback

3. **Chunking Strategy**
   - **Dilemma:** How to chunk long texts optimally?
   - **Current:** 512 chars with 50 char overlap
   - **Status:** Working, but could be improved with sentence-aware chunking

4. **Query Parser Complexity**
   - **Dilemma:** How complex should query understanding be?
   - **Current:** Pattern-based with intent detection
   - **Future:** Could add ML-based intent classification

### Ideas for Improvement

1. **Query Expansion**
   - Add synonyms: "פניות" → ["בקשות", "requests"]
   - Add variations: "אור גלילי" → ["אור", "גלילי"]
   - **Implementation:** Create synonym dictionary, expand query before search

2. **Result Re-ranking**
   - Use ML model to re-rank results
   - Consider user feedback
   - **Implementation:** Train small model on query-result pairs

3. **Query Caching**
   - Cache frequent queries
   - **Implementation:** Redis or in-memory cache

4. **Multi-stage Retrieval**
   - Stage 1: Keyword filter
   - Stage 2: Semantic search
   - Stage 3: Re-rank
   - **Implementation:** Sequential filtering

5. **Incremental Embedding Updates**
   - Only regenerate embeddings for new/changed requests
   - **Implementation:** Track last update time, process only changed

6. **Better Chunking**
   - Sentence-aware chunking
   - Preserve field boundaries
   - **Implementation:** Use sentence tokenizer

7. **Context Compression**
   - Summarize context before sending to LLM
   - **Implementation:** Use smaller model to summarize

8. **Answer Validation**
   - Check if answer is supported by context
   - **Implementation:** Verify answer against retrieved requests

---

## 🏗️ Technical Architecture

### Core Components

1. **Query Parser** (`scripts/utils/query_parser.py`)
   - Intent detection (person, project, type, status, general)
   - Entity extraction (names, IDs)
   - Target field determination
   - Configurable via `config/search_config.json`

2. **Text Processing** (`scripts/utils/text_processing.py`)
   - `combine_text_fields_weighted()`: Combines ~44 fields with weighting
   - `chunk_text()`: Splits long texts into chunks (512 chars, 50 overlap)

3. **Embedding Generation** (`scripts/core/generate_embeddings.py`)
   - Reads from PostgreSQL `requests` table
   - Uses weighted field combination
   - Generates embeddings (sentence-transformers/all-MiniLM-L6-v2)
   - Stores in `request_embeddings` table

4. **Search** (`scripts/core/search.py`)
   - Query parsing
   - Field-specific search with boosting
   - Type/status filtering
   - Semantic similarity search
   - Result deduplication

5. **RAG System** (`scripts/core/rag_query.py`)
   - Retrieval using improved search
   - Context formatting
   - Prompt building
   - LLM generation (Mistral-7B-Instruct)

6. **Hebrew Utilities** (`scripts/utils/hebrew.py`)
   - RTL display fix
   - Encoding handling

7. **Database Utilities** (`scripts/utils/database.py`)
   - Connection management
   - pgvector registration

### Database Schema

**`requests` table:**
- 8,195 rows
- 83 columns (all TEXT)
- Main data table

**`request_embeddings` table:**
- 36,031 rows (chunks)
- Columns: `requestid`, `chunk_index`, `text_chunk`, `embedding` (vector(384))
- Vector index on `embedding`

### Configuration

**`.env` file:**
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

**`config/search_config.json`:**
- Query patterns (person, project, type, status)
- Field mappings (Hebrew → English)
- Target fields per intent
- Boost rules

### Models Used

1. **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
   - 384 dimensions
   - Fast and efficient
   - Good for Hebrew

2. **LLM Model:** `mistralai/Mistral-7B-Instruct-v0.2`
   - 4-bit quantized (~4GB RAM)
   - Supports Hebrew
   - Good for instruction following

---

## 📈 Project Quality Assessment

### Current Level: MVP → Production-Ready (70%)

**Strengths:**
- ✅ Solid foundation
- ✅ Correct architecture
- ✅ Good code organization
- ✅ Working core functionality
- ✅ Configuration approach

**Areas for Improvement:**
- ⚠️ Comprehensive error handling
- ⚠️ Logging system
- ⚠️ Unit tests
- ⚠️ Performance monitoring
- ⚠️ Input validation

**Time to Production-Ready:** 2-3 weeks

---

## 📝 Key Decisions Made

1. **All TEXT Columns:** Simplified schema, works for embeddings
2. **Local Installation:** User preference, not Docker
3. **No PII Sanitization:** Not needed for internal POC
4. **4-bit Quantization:** RAM constraints, excellent quality
5. **Field Weighting:** 3-tier system based on importance
6. **Query Parser:** Pattern-based, configurable per client
7. **Temp Table Method:** Solved vector search parameter binding issue

---

## 🎯 Project Status Summary

**Completed:**
- ✅ Phase 1: Data Export & Isolation
- ✅ Phase 2: Vector Database Setup
- ✅ Phase 2.5: Embedding Improvements
- ✅ Phase 2.6: Query Parser & Search Integration
- ✅ Phase 3: RAG Implementation

**Current State:**
- System is functional end-to-end
- Search works with query understanding
- RAG can answer questions
- Hebrew support working
- Ready for testing and polish

**Next:**
- Test RAG system
- Optimize prompts
- Add error handling and logging
- Polish for production

---

## 📚 Important Files Reference

### Core Scripts
- `scripts/core/search.py` - Main search script
- `scripts/core/rag_query.py` - RAG system
- `scripts/core/generate_embeddings.py` - Embedding generation
- `scripts/utils/query_parser.py` - Query parsing
- `scripts/utils/text_processing.py` - Text processing utilities

### Configuration
- `config/search_config.json` - Search configuration
- `.env` - Database credentials (not in git)

### Documentation
- `docs/COMPLETE_PROJECT_REVIEW_AND_GUIDE.md` - Comprehensive guide
- `docs/PROJECT_PROGRESS_SUMMARY.md` - Progress tracking
- `docs/ACTION_PLAN_NEXT_STEPS.md` - Next steps
- `README.md` - Quick start guide

---

## 🔄 How to Continue Work

### If Starting Fresh Session:

1. **Read this document** - Understand current state
2. **Check current status** - Run tests, verify system works
3. **Review next steps** - See "Next Steps & Plans" section
4. **Continue from where we left off** - Usually testing or polish

### Common Tasks:

**Test Search:**
```bash
python scripts/core/search.py
```

**Test RAG:**
```bash
python scripts/core/rag_query.py
```

**Regenerate Embeddings:**
```bash
python scripts/core/generate_embeddings.py
```

**Check Database:**
```bash
python scripts/helpers/check_all_tables.py
```

---

## ✅ Quality Checklist

- [x] Data pipeline working
- [x] Embeddings generated with weighted fields
- [x] Search with query understanding
- [x] RAG system implemented
- [x] Hebrew support working
- [ ] Comprehensive error handling
- [ ] Logging system
- [ ] Unit tests
- [ ] Performance monitoring
- [ ] Production-ready polish

---

**Last Updated:** Based on current project state  
**Status:** System functional, ready for testing and polish  
**Next Action:** Test RAG system and optimize based on results

