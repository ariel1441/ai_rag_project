# 🚀 New Chat - Start Here

**Purpose:** This document provides everything a new chat session needs to know about the project, recent changes, and how to continue work.

**Last Updated:** After project transfer to new PC with GPU support

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Recent Changes - New PC Migration](#recent-changes---new-pc-migration)
3. [System Architecture](#system-architecture)
4. [Key Files & Their Purposes](#key-files--their-purposes)
5. [Important Documentation](#important-documentation)
6. [Current Status](#current-status)
7. [What to Know Before Continuing](#what-to-know-before-continuing)

---

## 🎯 Project Overview

### What This Project Is

A **Retrieval-Augmented Generation (RAG) system** for querying a database of requests/actions/transactions in Hebrew. The system:

1. **Semantic Search:** Uses embeddings to find semantically similar requests
2. **Natural Language Answers:** Uses LLM (Mistral-7B) to generate Hebrew answers
3. **Query Understanding:** Parses Hebrew queries to understand intent (person, project, type, status, etc.)
4. **Hybrid Search:** Combines SQL filtering with semantic similarity ranking

### Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL with pgvector extension
- **Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **LLM:** Mistral-7B-Instruct-v0.2 (for RAG answers)
- **Frontend:** Vanilla JavaScript/HTML/CSS
- **Deployment:** Local development (can be deployed to server)

### Main Use Case

Users can ask questions in Hebrew like:
- "פניות מאור גלילי" (requests from Ohr Galili)
- "כמה פניות יש מסוג 4?" (how many requests of type 4?)
- "תביא לי סיכום של כל הפניות" (bring me a summary of all requests)
- "פניות דומות ל-211000001" (requests similar to 211000001)

The system understands the query, searches the database, and provides natural language answers.

---

## 🔄 Recent Changes - New PC Migration

### What Was Done

The project was successfully transferred from a work PC to a personal PC with GPU support. Here's what changed:

#### 1. **Git Repository Setup**
- Created GitHub repo: `https://github.com/ariel1441/ai_rag_project.git`
- Excluded large files (models, .env, venv) from Git
- Models are auto-downloaded on first use
- All code is version-controlled

#### 2. **Database Setup (Docker)**
- **Problem:** pgvector extension was difficult to install manually on Windows
- **Solution:** Used Docker with `pgvector/pgvector:pg16` image
- **Port:** Database runs on port 5433 (to avoid conflicts with existing PostgreSQL)
- **Script:** `scripts/setup/setup_docker_postgres.py` automates setup

#### 3. **Data Import**
- CSV file (`requests.csv`) imported via Google Drive
- **Script:** `scripts/setup/import_data_from_csv.py`
- **Issue Fixed:** BOM character (`\ufeff`) in column names caused field matching issues
- **Solution:** Enhanced field matching in `text_processing.py` to handle BOM and case variations

#### 4. **Embeddings Import**
- **Original:** Generated ~40,000 chunks on work PC
- **New PC:** Imported pre-generated embeddings (40k chunks) via CSV
- **Note:** Generating new embeddings on new PC only produced ~26,000 chunks due to CSV having fewer populated fields
- **Workaround:** Imported the embedded CSV from work PC
- **Status:** Currently has 40k embeddings in `request_embeddings` table

#### 5. **GPU Optimization**
- **Added:** `scripts/core/rag_query_gpu.py` - GPU-optimized RAG system
- **Updated:** `api/services.py` to use GPU-optimized version automatically
- **Features:**
  - Automatic GPU detection
  - 500 token answers (vs 200 on CPU)
  - Sampling with temperature (vs greedy decoding on CPU)
  - Much faster inference (3-10s vs 15-30s on CPU)

#### 6. **Field Matching Improvements**
- **Problem:** CSV import had different column names (BOM, case variations)
- **Solution:** Enhanced `get_value()` function in `text_processing.py`:
  - Handles BOM characters (`\ufeff`)
  - Case-insensitive matching
  - Underscore/hyphen variations
  - Multiple matching strategies

#### 7. **Test Scripts Created**
- `scripts/tests/test_embedding_chunk_count.py` - Verifies embedding logic produces ~40k chunks
- `scripts/tests/test_rag_comprehensive.py` - Comprehensive RAG test suite
- `scripts/tests/diagnose_embedding_issue.py` - Diagnoses embedding field matching issues

#### 8. **Documentation**
- `docs/START_RAG_SERVER_AND_TEST.md` - How to start server and test
- `docs/TRANSFER_TO_NEW_PC_GUIDE.md` - Complete transfer guide
- `docs/GENERIC_EMBEDDING_COMPLETE_GUIDE.md` - Generic embedding setup for new clients

### Files Changed/Added for Migration

**New Files:**
- `scripts/setup/setup_docker_postgres.py` - Docker PostgreSQL setup
- `scripts/setup/import_data_from_csv.py` - CSV import with BOM handling
- `scripts/core/rag_query_gpu.py` - GPU-optimized RAG
- `scripts/tests/test_embedding_chunk_count.py` - Embedding verification
- `scripts/tests/test_rag_comprehensive.py` - RAG test suite
- `scripts/core/generate_embeddings_original_backup.py` - Backup of original embedding script

**Modified Files:**
- `api/services.py` - Now uses GPU-optimized RAG automatically
- `scripts/utils/text_processing.py` - Enhanced field matching
- `scripts/core/generate_embeddings.py` - Improved ID column detection, BOM handling
- `.gitignore` - Excludes models, .env, venv

**Configuration:**
- `.env` file (not in Git) - Contains database credentials
- Docker runs on port 5433 (default PostgreSQL is 5432)

---

## 🏗️ System Architecture

### High-Level Flow

```
User Query (Hebrew)
    ↓
[Query Parser] → Intent, Entities, Query Type
    ↓
[Search Service] → SQL Filters + Semantic Search
    ↓
[Retrieval] → Top-K Relevant Requests
    ↓
[RAG System] → LLM Generates Answer (if use_llm=True)
    ↓
Response: Answer + List of Requests
```

### Components

1. **Query Parser** (`scripts/utils/query_parser.py`)
   - Detects intent: person, project, type, status, general
   - Extracts entities: names, IDs, dates, urgency flags
   - Determines query type: find, count, summarize, similar, urgent, answer_retrieval

2. **Search Service** (`api/services.py` - `SearchService`)
   - Hybrid search: SQL filters + semantic similarity
   - Field-specific boosting (exact matches get 2.0x boost)
   - Handles similar requests by request ID

3. **RAG Service** (`api/services.py` - `RAGService`)
   - Uses `GPUOptimizedRAGSystem` (or falls back to `RAGSystem`)
   - Retrieves relevant requests
   - Generates natural language answers using Mistral-7B

4. **Embedding Generation** (`scripts/core/generate_embeddings.py`)
   - Combines ~44 fields with weights (3.0x, 2.0x, 1.0x, 0.5x)
   - Chunks text (512 chars, 50 overlap)
   - Generates embeddings using sentence-transformers
   - Stores in `request_embeddings` table

5. **Text Processing** (`scripts/utils/text_processing.py`)
   - `combine_text_fields_weighted()` - Combines fields with weights
   - `chunk_text()` - Splits long text into chunks
   - Handles BOM characters and case variations

### Database Schema

**Main Tables:**
- `requests` - Source data (8,195 requests)
- `request_embeddings` - Vector embeddings (40,000 chunks)
  - `requestid` - Foreign key to requests
  - `chunk_index` - Index of chunk within request
  - `text_chunk` - The text that was embedded
  - `embedding` - Vector (384 dimensions, pgvector type)

**Indexes:**
- IVFFlat index on embeddings for fast similarity search
- Indexes on requestid, chunk_index

---

## 📁 Key Files & Their Purposes

### Core RAG System
- `scripts/core/rag_query.py` - Base RAG system (CPU-optimized)
- `scripts/core/rag_query_gpu.py` - GPU-optimized RAG system (use this on GPU)
- `scripts/core/generate_embeddings.py` - Generate embeddings from requests table

### API & Services
- `api/app.py` - FastAPI application, endpoints
- `api/services.py` - SearchService and RAGService
- `api/models.py` - Pydantic models for requests/responses
- `api/frontend/` - Web interface (HTML, JS, CSS)

### Utilities
- `scripts/utils/query_parser.py` - Query parsing and intent detection
- `scripts/utils/text_processing.py` - Text combination and chunking
- `config/search_config.json` - Query patterns and field mappings

### Setup Scripts
- `scripts/setup/setup_docker_postgres.py` - Docker PostgreSQL setup
- `scripts/setup/import_data_from_csv.py` - CSV import
- `scripts/setup/setup_embeddings.py` - Generic embedding setup wizard

### Test Scripts
- `scripts/tests/test_rag_comprehensive.py` - Comprehensive RAG tests
- `scripts/tests/test_embedding_chunk_count.py` - Verify embedding logic
- `scripts/tests/test_comprehensive_search_accuracy.py` - Search accuracy tests

### Configuration
- `.env` - Database credentials, API keys (NOT in Git)
- `config/search_config.json` - Query patterns
- `config/embedding_config.json` - Embedding configuration (for generic setup)

---

## 📚 Important Documentation

### Must Read (In Order)

1. **`docs/START_RAG_SERVER_AND_TEST.md`**
   - How to start the API server
   - How to test RAG queries
   - GPU detection and performance expectations

2. **`docs/SEARCH_IMPROVEMENTS_COMPLETE_SUMMARY.md`**
   - Complete explanation of search logic
   - 3-layer hybrid search architecture
   - SQL filters, text filters, semantic ranking

3. **`docs/ALL_FIXES_SUMMARY.md`**
   - Summary of all fixes made to search system
   - Generic nature of fixes (not hard-coded)

4. **`docs/TRANSFER_TO_NEW_PC_GUIDE.md`**
   - Complete guide for transferring project
   - Database setup, model handling, Git workflow

### Additional Important Docs

- **`docs/HOW_SEARCH_AND_RAG_WORK.md`** - Explains search vs RAG
- **`docs/RAG_RESULT_TYPES_EXPLAINED.md`** - What each query type returns
- **`docs/EMBEDDING_SETUP_GUIDE.md`** - Generic embedding setup for new clients
- **`docs/GENERIC_EMBEDDING_COMPLETE_GUIDE.md`** - Full generic embedding process
- **`docs/RAG_SYSTEM_POTENTIAL_AND_CAPABILITIES.md`** - Future possibilities

### Feature Documentation

- **`docs/QUERY_HISTORY_FEATURE_SUMMARY.md`** - Query history feature
- **`docs/FEATURE_IDEAS_AND_ROADMAP.md`** - Future feature ideas
- **`docs/FEATURE_IMPLEMENTATION_GUIDES.md`** - Implementation guides

---

## ✅ Current Status

### What's Working

✅ **Database:** PostgreSQL with pgvector, 40k embeddings loaded  
✅ **API Server:** FastAPI running, GPU-optimized RAG enabled  
✅ **Search:** Hybrid search working (SQL + semantic)  
✅ **RAG:** LLM answers working, GPU detection automatic  
✅ **Query Parser:** Handles all query types (find, count, summarize, similar, urgent)  
✅ **Field Matching:** Robust handling of BOM, case variations  
✅ **Test Scripts:** Comprehensive test suite available  

### Known Issues / Notes

⚠️ **Embedding Generation:** New embeddings on new PC produce ~26k chunks (vs 40k) due to CSV having fewer populated fields. Workaround: Import pre-generated embeddings.

⚠️ **First RAG Query:** Takes 30-60 seconds (model loading). Subsequent queries are fast (3-10s with GPU).

✅ **GPU Support:** Automatic detection, falls back to CPU if needed.

### Environment

- **Database:** Docker PostgreSQL on port 5433
- **API:** FastAPI on port 8000
- **GPU:** Available and being used (if detected)
- **Models:** Auto-downloaded on first use (not in Git)

---

## 🎓 What to Know Before Continuing

### Critical Information

1. **Database Connection:**
   - Host: `localhost`
   - Port: `5433` (Docker) or `5432` (if using local PostgreSQL)
   - Database: `ai_requests_db`
   - User: `postgres`
   - Password: In `.env` file (not in Git)

2. **Embeddings:**
   - Currently has 40k chunks (imported from work PC)
   - Table: `request_embeddings`
   - If regenerating, expect ~26k chunks (CSV has fewer fields)

3. **GPU Usage:**
   - Automatic detection in `rag_query_gpu.py`
   - API uses GPU-optimized version automatically
   - Falls back to CPU if GPU not available

4. **Query Types Supported:**
   - `find` - Find requests (default)
   - `count` - Count requests ("כמה...?")
   - `summarize` - Summarize requests
   - `similar` - Find similar requests
   - `urgent` - Urgent requests
   - `answer_retrieval` - Retrieve answers from similar requests

5. **Field Weights:**
   - 3.0x: Critical fields (projectname, updatedby, requesttypeid, etc.) - repeated 3 times
   - 2.0x: Important fields (createddate, contact names, etc.) - repeated 2 times
   - 1.0x: Supporting fields - included once
   - 0.5x: Booleans, coordinates - included once

### Important Principles

1. **Generic Code:** All fixes are generic and logic-based, not hard-coded for specific cases
2. **Modular Features:** New features (like query history) are modular and easily removable
3. **Backward Compatibility:** Changes don't break existing functionality
4. **Testing:** Always test changes before committing

### Common Tasks

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

**Generate Embeddings (if needed):**
```powershell
python scripts/core/generate_embeddings.py
```

### Git Workflow

- **Models:** NOT in Git (auto-download)
- **.env:** NOT in Git (contains secrets)
- **Code:** All in Git
- **Data:** CSV files can be shared via Google Drive or other means

### When Making Changes

1. **Test locally first** - Use test scripts
2. **Verify GPU usage** - Check terminal output
3. **Check database** - Verify queries work
4. **Test via web interface** - Manual testing
5. **Commit with descriptive messages** - Include what and why

---

## 🚀 Quick Start for New Chat

1. **Read this document** (you're doing it!)
2. **Read `docs/START_RAG_SERVER_AND_TEST.md`** - How to run and test
3. **Read `docs/SEARCH_IMPROVEMENTS_COMPLETE_SUMMARY.md`** - Understand search logic
4. **Check current status** - Run test scripts to verify everything works
5. **Understand the codebase** - Review key files listed above
6. **Ask questions** - If something is unclear, ask before making changes

---

## 📝 Notes for Future Development

### Things to Remember

- **Hebrew Support:** All queries are in Hebrew, system handles Hebrew text
- **Field Matching:** Must handle BOM characters, case variations, naming conventions
- **GPU First:** Always use GPU-optimized version when available
- **Generic Design:** Keep code generic for future clients/projects
- **Testing:** Comprehensive test suite exists, use it

### Future Enhancements (Not Yet Implemented)

- Prediction capabilities (approval/rejection prediction)
- Automatic actions based on DB knowledge
- Trend forecasting
- Auto-response generation from past interactions

See `docs/RAG_SYSTEM_POTENTIAL_AND_CAPABILITIES.md` for details.

---

## 🔗 Quick Links

- **GitHub Repo:** `https://github.com/ariel1441/ai_rag_project.git`
- **API Docs:** `http://localhost:8000/docs` (when server running)
- **Web Interface:** `api/frontend/index.html` or `http://localhost:8000/`

---

## ❓ Questions?

If you're unsure about something:
1. Check the relevant documentation file
2. Look at the code comments
3. Run test scripts to see how things work
4. Ask for clarification before making changes

**Remember:** The system is working well. Be careful not to break existing functionality when making changes!

---

**Last Updated:** After successful migration to new PC with GPU support  
**Status:** ✅ System fully operational, ready for development

