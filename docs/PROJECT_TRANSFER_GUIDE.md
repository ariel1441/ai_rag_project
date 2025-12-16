# Project Transfer Guide - Moving to Personal PC

## 🎯 Overview

This guide helps you transfer the entire project (with embeddings and RAG) to your personal PC in the most efficient way.

---

## 📊 What Needs to Be Transferred

### ✅ Small Files (Transfer via USB/Network):

1. **Code Files** (~50MB)
   - All Python scripts
   - Configuration files
   - Documentation
   - **Location:** Entire project folder (except models)

2. **Database** (varies)
   - PostgreSQL database dump
   - Includes: requests table + embeddings table
   - **Size:** Depends on data (probably 100-500MB)

3. **Configuration Files**
   - `.env` file (database credentials)
   - `config/` folder
   - **Size:** <1MB

### ⚠️ Large Files (Models - Decision Needed):

1. **Embedding Model** (~90MB)
   - **Name:** `sentence-transformers/all-MiniLM-L6-v2`
   - **Location:** `~/.cache/huggingface/hub/` (auto-downloaded)
   - **Recommendation:** ✅ **Download automatically** (small, fast)

2. **LLM Model** (~4-7GB)
   - **Name:** `mistral-7b-instruct`
   - **Location:** `models/llm/mistral-7b-instruct/`
   - **Recommendation:** ⚠️ **Upload if possible** (large, slow download)

---

## 🚀 Recommended Approach

### Option 1: Upload Models (Recommended if you have good upload speed)

**Why:**
- Faster setup on new PC
- No need to wait for downloads
- Works offline

**Steps:**
1. Copy entire `models/` folder to USB/external drive
2. Transfer to new PC
3. Place in same location
4. Models ready immediately

**Time:** ~10-30 minutes (depending on transfer speed)

---

### Option 2: Download Automatically (Recommended if upload is slow)

**Why:**
- No need to transfer large files
- Automatic download on first use
- Models cached for future use

**Steps:**
1. Don't transfer `models/` folder
2. Run scripts on new PC
3. Models download automatically on first use
4. Cached for future runs

**Time:** 
- Embedding model: ~2-5 minutes
- LLM model: ~30-60 minutes (depending on internet)

---

## 📋 Complete Transfer Checklist

### Step 1: Prepare on Work PC

#### 1.1: Export Database
```bash
# Create database dump
pg_dump -h localhost -p 5433 -U postgres -d ai_requests_db -F c -f database_backup.dump
```

**What it includes:**
- All tables (requests, request_embeddings, etc.)
- All data
- All indexes

**Size:** ~100-500MB (depends on data)

#### 1.2: Copy Project Files
```bash
# Copy entire project (excluding models if you want to download)
# Or include models if you want to upload them
```

**What to copy:**
- ✅ All Python scripts
- ✅ All config files
- ✅ All documentation
- ✅ `.env` file (or create new one)
- ⚠️ `models/` folder (optional - see recommendations above)

#### 1.3: Check Model Sizes
```bash
# Check LLM model size
Get-ChildItem -Path "models\llm\mistral-7b-instruct" -Recurse | Measure-Object -Property Length -Sum
```

**Expected:**
- LLM model: ~4-7GB
- Embedding model: Not in project (auto-downloaded)

---

### Step 2: Transfer to Personal PC

#### Option A: USB/External Drive (Recommended for Models)

1. **Copy to USB:**
   - Project folder (without `models/` if downloading)
   - OR Project folder (with `models/` if uploading)
   - Database dump file

2. **Transfer to Personal PC:**
   - Copy from USB to desired location
   - Example: `C:\ai_learning\train_ai_tamar_request\`

#### Option B: Network Transfer

1. **Share folder on work PC**
2. **Copy over network to personal PC**
3. **Faster if on same network**

#### Option C: Cloud Storage (if allowed)

1. **Upload to OneDrive/Google Drive**
2. **Download on personal PC**
3. **Useful for large files**

---

### Step 3: Setup on Personal PC

#### 3.1: Install Prerequisites

**PostgreSQL:**
```bash
# Download and install PostgreSQL
# Or use Docker:
docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=password pgvector/pgvector:pg16
```

**Python:**
```bash
# Install Python 3.8+
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate.ps1
```

**Python Packages:**
```bash
pip install psycopg2-binary sentence-transformers numpy tqdm python-dotenv transformers torch
```

**Time:** 15-30 minutes

#### 3.2: Enable pgvector Extension

```sql
-- Connect to PostgreSQL
psql -U postgres -d your_database

-- Enable extension
CREATE EXTENSION vector;
```

**Time:** 1 minute

#### 3.3: Import Database

```bash
# Restore database
pg_restore -h localhost -p 5433 -U postgres -d ai_requests_db -c database_backup.dump
```

**What it does:**
- Creates all tables
- Imports all data
- Creates all indexes (including vector indexes)

**Time:** 5-15 minutes (depends on data size)

#### 3.4: Setup .env File

Create `.env` file:
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

**Time:** 1 minute

#### 3.5: Models Setup

**If you uploaded models:**
- ✅ Models already in place
- ✅ Ready to use immediately
- ✅ No download needed

**If downloading automatically:**
- Models will download on first use:
  - Embedding model: First search/embedding generation (~2-5 min)
  - LLM model: First RAG query (~30-60 min)

---

## 🎯 Recommended Transfer Strategy

### Best Approach (Hybrid):

1. **Upload LLM Model** (if possible)
   - Large file (~4-7GB)
   - Slow to download
   - Transfer via USB/external drive

2. **Download Embedding Model Automatically**
   - Small file (~90MB)
   - Fast download
   - Auto-downloads on first use

3. **Transfer Everything Else**
   - Code, config, database
   - Small files, fast transfer

---

## 📁 File Structure on New PC

```
C:\ai_learning\train_ai_tamar_request\
├── scripts/
│   ├── core/
│   │   ├── generate_embeddings.py
│   │   ├── rag_query.py
│   │   └── search.py
│   ├── setup/
│   └── utils/
├── config/
│   ├── search_config.json
│   └── embedding_config.json (if using generic)
├── models/
│   └── llm/
│       └── mistral-7b-instruct/  ← Upload this if possible
├── .env
├── database_backup.dump
└── docs/
```

---

## 🔍 Model Locations & Sizes

### Embedding Model:
- **Name:** `sentence-transformers/all-MiniLM-L6-v2`
- **Size:** ~90MB
- **Location:** `~/.cache/huggingface/hub/` (auto-downloaded)
- **Download:** Automatic on first use
- **Recommendation:** ✅ Download automatically

### LLM Model:
- **Name:** `mistral-7b-instruct`
- **Size:** ~4-7GB (depending on format)
- **Location:** `models/llm/mistral-7b-instruct/`
- **Download:** Manual or automatic (if not present)
- **Recommendation:** ⚠️ Upload if possible (large file)

---

## 🚀 Quick Setup Script

Creating a setup script to automate the process:

