# Transfer Project to New PC - Complete Guide

## 🎯 Goal

Transfer your complete project (with embeddings and RAG) to your personal PC and get it running.

---

## 📊 What Needs Transferring

### Models (The Big Files):

1. **Embedding Model** (~90MB)
   - **Name:** `sentence-transformers/all-MiniLM-L6-v2`
   - **Location:** Auto-downloaded to `~/.cache/huggingface/hub/`
   - **Recommendation:** ✅ **Download automatically** (small, fast, ~2-5 min)

2. **LLM Model** (~4-7GB)
   - **Name:** `mistral-7b-instruct`
   - **Location:** `models/llm/mistral-7b-instruct/`
   - **Recommendation:** ⚠️ **Upload if possible** (large, slow download ~30-60 min)

### Everything Else (Small Files):

- ✅ All Python scripts (~10MB)
- ✅ Configuration files (~1MB)
- ✅ Documentation (~5MB)
- ✅ Database dump (~100-500MB, depends on data)

**Total (without models):** ~120-520MB

---

## 🚀 Recommended Strategy

### Best Approach: Hybrid

1. **Upload LLM Model** (if you have USB/external drive)
   - Copy `models/llm/mistral-7b-instruct/` folder
   - ~4-7GB, but saves 30-60 minutes of download time

2. **Download Embedding Model Automatically**
   - Small (~90MB)
   - Fast download (~2-5 minutes)
   - Auto-downloads on first use

3. **Transfer Everything Else**
   - Code, config, database
   - Small files, fast transfer

---

## 📋 Step-by-Step Transfer Process

### STEP 1: On Work PC - Prepare for Transfer

#### 1.1: Export Database

```bash
# Create database dump (includes all tables + data + indexes)
pg_dump -h localhost -p 5433 -U postgres -d ai_requests_db -F c -f database_backup.dump
```

**What it includes:**
- `requests` table (all your data)
- `request_embeddings` table (all embeddings)
- All indexes (including vector indexes)
- All other tables

**Size:** ~100-500MB (depends on data)

**Time:** 2-5 minutes

#### 1.2: Check Model Sizes

```powershell
# Check LLM model size
Get-ChildItem -Path "models\llm\mistral-7b-instruct" -Recurse -File | 
    Measure-Object -Property Length -Sum | 
    Select-Object @{Name="SizeGB";Expression={[math]::Round($_.Sum/1GB, 2)}}
```

**Expected:** ~4-7GB

#### 1.3: Prepare Transfer Package

**Option A: With Models (Recommended if you have USB/external drive)**
```
Transfer Package:
├── Project folder (entire folder)
│   ├── scripts/
│   ├── config/
│   ├── models/          ← Include this (4-7GB)
│   ├── .env
│   └── docs/
└── database_backup.dump
```

**Option B: Without Models (Download automatically)**
```
Transfer Package:
├── Project folder (without models/)
│   ├── scripts/
│   ├── config/
│   ├── .env
│   └── docs/
└── database_backup.dump
```

**Size:**
- With models: ~5-8GB
- Without models: ~120-520MB

---

### STEP 2: Transfer to Personal PC

#### Option A: USB/External Drive (Recommended for Models)

1. **Copy to USB:**
   - Entire project folder (with or without `models/`)
   - `database_backup.dump` file

2. **Transfer to Personal PC:**
   - Copy from USB to desired location
   - Example: `C:\ai_learning\train_ai_tamar_request\`

**Time:** 10-30 minutes (depends on USB speed and model size)

#### Option B: Network Transfer

1. **Share folder on work PC**
2. **Copy over network to personal PC**
3. **Faster if on same network**

**Time:** 5-15 minutes (depends on network speed)

#### Option C: Cloud Storage (if allowed)

1. **Upload to OneDrive/Google Drive**
2. **Download on personal PC**
3. **Useful for large files**

**Time:** Depends on upload/download speed

---

### STEP 3: Setup on Personal PC

#### 3.1: Install PostgreSQL

**Option A: Installer**
- Download: https://www.postgresql.org/download/windows/
- Install with default settings
- **Time:** 10-20 minutes

**Option B: Docker (Easiest)**
```bash
docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=password pgvector/pgvector:pg16
```
- **Time:** 5 minutes
- **Includes:** PostgreSQL + pgvector extension

#### 3.2: Enable pgvector Extension

```sql
-- Connect to PostgreSQL
psql -U postgres -d postgres

-- Create database
CREATE DATABASE ai_requests_db;

-- Connect to database
\c ai_requests_db

-- Enable pgvector
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
- Imports all data (requests + embeddings)
- Creates all indexes (including vector indexes)

**Time:** 5-15 minutes (depends on data size)

**Verify:**
```sql
-- Check tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Check embeddings count
SELECT COUNT(*) FROM request_embeddings;
```

#### 3.4: Setup Python Environment

```bash
# Navigate to project folder
cd C:\ai_learning\train_ai_tamar_request

# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\activate.ps1

# Install packages
pip install psycopg2-binary sentence-transformers numpy tqdm python-dotenv transformers torch
```

**Time:** 5-10 minutes

**What gets downloaded:**
- Python packages (~200-500MB)
- Embedding model will download on first use (~90MB)

#### 3.5: Create .env File

Create `.env` file in project root:
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

**Time:** 1 minute

#### 3.6: Verify Setup

```bash
# Run setup check script
python scripts/setup/setup_new_pc.py
```

**What it checks:**
- ✅ Python version
- ✅ Python packages
- ✅ Database connection
- ✅ pgvector extension
- ✅ Tables exist
- ✅ Embeddings count
- ✅ Models present

**Time:** 1 minute

---

## 🔍 Model Handling Details

### Embedding Model (Auto-Download Recommended)

**Why download automatically:**
- Small file (~90MB)
- Fast download (~2-5 minutes)
- Always up-to-date
- No manual transfer needed

**When it downloads:**
- First time you run: `python scripts/core/search.py`
- First time you run: `python scripts/core/generate_embeddings.py`
- Automatically cached for future use

**Location on new PC:**
- `C:\Users\YourName\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2\`

**No action needed** - it just works!

---

### LLM Model (Upload Recommended)

**Why upload if possible:**
- Large file (~4-7GB)
- Slow download (~30-60 minutes)
- Faster setup if uploaded

**If you upload:**
1. Copy `models/llm/mistral-7b-instruct/` folder
2. Place in same location on new PC
3. Ready immediately - no download needed

**If you don't upload:**
1. Model downloads automatically on first RAG query
2. Takes ~30-60 minutes
3. Cached for future use

**Location on new PC:**
- `C:\ai_learning\train_ai_tamar_request\models\llm\mistral-7b-instruct\`

---

## ⚡ Quick Start Commands

### After Setup, Test Everything:

```bash
# 1. Activate virtual environment
.\venv\Scripts\activate.ps1

# 2. Check setup
python scripts/setup/setup_new_pc.py

# 3. Test search (embedding model downloads if needed)
python scripts/core/search.py

# 4. Test RAG (LLM model downloads if not present)
python scripts/core/rag_query.py
```

---

## 📊 Time Estimates

### Transfer Phase:
- Export database: 2-5 minutes
- Copy files to USB: 10-30 minutes (with models) or 2-5 minutes (without)
- Transfer to new PC: 10-30 minutes (with models) or 2-5 minutes (without)
- **Total:** 22-65 minutes (with models) or 4-10 minutes (without)

### Setup Phase:
- Install PostgreSQL: 10-20 minutes
- Enable pgvector: 1 minute
- Import database: 5-15 minutes
- Install Python packages: 5-10 minutes
- Create .env: 1 minute
- Verify setup: 1 minute
- **Total:** 18-47 minutes

### Model Download (if not uploaded):
- Embedding model: 2-5 minutes (on first use)
- LLM model: 30-60 minutes (on first RAG query)

**Grand Total:**
- **With models uploaded:** ~40-112 minutes (~1-2 hours)
- **Without models (download):** ~24-57 minutes + 32-65 minutes download = ~1-2 hours

**Both approaches take similar time!** Choose based on your preference.

---

## 🎯 Recommended Approach

### For Best Experience:

1. **Upload LLM Model** (if you have USB/external drive)
   - Saves download time
   - Works offline
   - Faster first RAG query

2. **Download Embedding Model Automatically**
   - Small file, fast download
   - No manual transfer needed
   - Always up-to-date

3. **Transfer Everything Else**
   - Code, config, database
   - Small files, fast transfer

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Python 3.8+ installed
- [ ] All packages installed
- [ ] PostgreSQL running
- [ ] pgvector extension enabled
- [ ] Database imported
- [ ] Tables exist (requests, request_embeddings)
- [ ] Embeddings count matches
- [ ] .env file created
- [ ] Models present (or will download)
- [ ] Setup check script passes

---

## 🆘 Troubleshooting

### Database Import Fails:
- Check PostgreSQL is running
- Check database exists
- Check user has permissions
- Try: `pg_restore -h localhost -p 5433 -U postgres -d ai_requests_db -c -v database_backup.dump`

### Models Not Found:
- **Embedding model:** Will download automatically on first use
- **LLM model:** 
  - If uploaded: Check path is correct
  - If not uploaded: Will download on first RAG query

### Connection Errors:
- Check `.env` file has correct credentials
- Check PostgreSQL is running
- Check port is correct (5433)

---

## 📝 Summary

**What to Transfer:**
- ✅ Code files (all scripts)
- ✅ Configuration files
- ✅ Database dump
- ⚠️ LLM model (recommended to upload if possible)
- ❌ Embedding model (download automatically)

**What Gets Downloaded:**
- Embedding model: ~90MB (on first use, ~2-5 min)
- LLM model: ~4-7GB (if not uploaded, ~30-60 min)

**Total Setup Time:**
- With models uploaded: ~1-2 hours
- Without models: ~1-2 hours (includes download time)

**Result:**
- Complete working project on new PC
- All embeddings preserved
- RAG system ready
- Everything works exactly as before

