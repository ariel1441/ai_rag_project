# Setup Guide for New User / New Project

**Purpose:** Complete step-by-step guide to set up this project on a new machine or for a new project.

**Time Required:** 1-2 hours (depending on data size and internet speed)

---

## 📋 Prerequisites Checklist

Before starting, make sure you have:

- [ ] **Python 3.10+** (3.11 or 3.12 recommended)
- [ ] **PostgreSQL 18** (or 15+) installed
- [ ] **pgvector extension** installed for PostgreSQL
- [ ] **Git** (optional, if cloning from repository)
- [ ] **8GB+ RAM** (for embedding generation and RAG)
- [ ] **10GB+ free disk space** (for database, models, embeddings)

---

## 🚀 Step-by-Step Setup

### Step 1: Get the Project Folder

**If you received the folder:**
- Extract/download the entire project folder
- Place it in a convenient location (e.g., `C:\Projects\train_ai_tamar_request\` or `~/projects/train_ai_tamar_request/`)
- Note the full path - you'll need it

**Verify you have these folders:**
- `scripts/` - Python scripts
- `api/` - API server code
- `config/` - Configuration files
- `docs/` - Documentation

---

### Step 2: Install Python Dependencies

**Open terminal/command prompt in the project folder:**

**Windows (PowerShell):**
```powershell
# Navigate to project folder
cd C:\Projects\train_ai_tamar_request  # (or your path)

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# If requirements.txt doesn't exist, install manually:
pip install psycopg2-binary pgvector sentence-transformers torch transformers fastapi uvicorn python-dotenv numpy pandas tqdm
```

**Linux/Mac:**
```bash
# Navigate to project folder
cd ~/projects/train_ai_tamar_request  # (or your path)

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Expected time:** 5-10 minutes (downloads packages)

**Troubleshooting:**
- If `python` doesn't work, try `python3`
- If `pip` doesn't work, try `python -m pip`
- On Windows, you may need to run PowerShell as Administrator

---

### Step 3: Set Up PostgreSQL Database

#### 3.1 Install PostgreSQL

**Windows:**
1. Download from: https://www.postgresql.org/download/windows/
2. Run installer
3. During installation:
   - Set port (default: 5432)
   - Set password for `postgres` user (remember this!)
   - Complete installation

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql-18 postgresql-contrib
```

**Mac:**
```bash
brew install postgresql@18
```

#### 3.2 Install pgvector Extension

**Windows:**
- Download from: https://github.com/pgvector/pgvector/releases
- Follow Windows installation guide
- Or use pre-built binaries if available

**Linux:**
```bash
# Follow pgvector installation guide
# Usually: git clone, make, make install
```

**Mac:**
```bash
brew install pgvector
```

#### 3.3 Create Database and Enable Extension

**Open PostgreSQL command line:**

**Windows:**
- Open "SQL Shell (psql)" from Start Menu
- Or use pgAdmin (GUI tool)

**Linux/Mac:**
```bash
sudo -u postgres psql
```

**Run these commands:**
```sql
-- Create database
CREATE DATABASE ai_requests_db;

-- Connect to the new database
\c ai_requests_db

-- Enable pgvector extension
CREATE EXTENSION vector;

-- Verify extension is installed
\dx vector

-- Should show: vector | 1.0 | public | ...
```

**If you get an error about pgvector:**
- Make sure pgvector is installed
- Restart PostgreSQL service
- Check PostgreSQL version compatibility

**Exit psql:**
```sql
\q
```

---

### Step 4: Configure Environment Variables

**Create `.env` file in the project root:**

**Windows (PowerShell):**
```powershell
# In project root folder
New-Item -Path .env -ItemType File
notepad .env
```

**Linux/Mac:**
```bash
touch .env
nano .env  # or use your preferred editor
```

**Add this content to `.env`:**

```env
# PostgreSQL Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here

# API Configuration (optional, for API server)
API_KEY=your_secure_api_key_here
```

**Important:**
- Replace `your_password_here` with your actual PostgreSQL password
- Replace `your_secure_api_key_here` with a random secure string (e.g., `abc123xyz789`)
- **Never commit `.env` to git!**

**Save and close the file.**

---

### Step 5: Prepare Your Data

#### 5.1 Export Data from Your Source Database

**If you have SQL Server:**
- Export your `Requests` table (or equivalent) to CSV
- Ensure UTF-8 encoding for Hebrew/Unicode support
- Save as: `data/raw/requests.csv`

**If you have another database:**
- Export to CSV format
- Ensure all columns are included
- Save as: `data/raw/requests.csv`

**If you already have CSV:**
- Place it in: `data/raw/requests.csv`
- Create `data/raw/` folder if it doesn't exist

#### 5.2 Verify CSV Format

- Open CSV in Excel or text editor
- Check that first row has column headers
- Verify Hebrew text displays correctly
- Note the number of rows (you'll need this later)

---

### Step 6: Import Data to PostgreSQL

**Make sure virtual environment is activated:**

**Windows:**
```powershell
.\venv\Scripts\activate.ps1
python scripts/helpers/import_csv_to_postgres.py
```

**Linux/Mac:**
```bash
source venv/bin/activate
python scripts/helpers/import_csv_to_postgres.py
```

**The script will:**
1. Ask for CSV file path (or use default: `data/raw/request.csv`)
2. Read the CSV file
3. Create `requests` table in PostgreSQL
4. Import all data
5. Validate import
6. Report statistics

**Expected output:**
```
Importing data...
✓ Created requests table
✓ Imported X rows
✓ Validation passed
```

**If you get errors:**
- Check `.env` file (database credentials correct?)
- Verify PostgreSQL is running: `Get-Service postgresql*` (Windows) or `sudo systemctl status postgresql` (Linux)
- Check CSV file path
- Ensure CSV has headers (column names in first row)

**Verify import:**
```sql
-- Connect to database
psql -U postgres -d ai_requests_db

-- Check row count
SELECT COUNT(*) FROM requests;
-- Should match your CSV row count
```

---

### Step 7: Generate Embeddings

**This is the most time-consuming step (30-60 minutes for 8K requests):**

```bash
# Make sure virtual environment is activated
python scripts/core/generate_embeddings.py
```

**What it does:**
1. Reads all requests from database
2. Combines fields with weighting (~44 fields)
3. Chunks long texts (512 chars, 50 overlap)
4. Generates embeddings using sentence-transformers model
5. Stores in `request_embeddings` table
6. Creates vector index for fast search

**Expected output:**
```
Generating embeddings...
Loading model: sentence-transformers/all-MiniLM-L6-v2
Processing request 1/8195...
Processing request 2/8195...
...
✓ Generated X embeddings
✓ Created vector index
```

**Time:** 
- 8,195 requests: ~30-60 minutes
- Depends on CPU speed and number of requests

**Progress:** You'll see progress bar or request numbers

**If you get errors:**
- Check database connection (`.env` file)
- Verify `requests` table exists and has data
- Check available RAM (needs ~2-4GB free)
- Make sure sentence-transformers model downloads (first time only)

**Verify embeddings:**
```sql
-- Check embeddings count
SELECT COUNT(*) FROM request_embeddings;
-- Should be 3-5x number of requests (due to chunking)
```

---

### Step 8: (Optional) Download LLM Model for RAG

**Only needed if you want to use RAG (textual answers):**

**The model is large (~7GB), so this is optional:**

**Option A: Automatic Download**
```bash
python scripts/core/download_rag_model.py
```

**Option B: Manual Download**
1. Go to: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2
2. Download model files
3. Place in: `models/llm/mistral-7b-instruct/`

**If you skip this:**
- ✅ Search will still work (retrieval-only, fast)
- ❌ RAG (textual answers) won't work until model is downloaded
- You can download it later when needed

**Note:** Model download is ~7GB and may take 30-60 minutes depending on internet speed.

---

### Step 9: Test the System

#### 9.1 Test Search (Fast, No LLM Needed)

**Option A: Using Python Script**
```bash
python scripts/core/search.py
```

Enter a query like: "פניות מאור גלילי" or "requests from John"

**Expected:** List of relevant requests

**Option B: Using API Server**
```bash
# Start API server
cd api
python -m uvicorn app:app --reload --port 8000
```

Then:
- Open browser: `http://localhost:8000` (frontend)
- Or use API: `http://localhost:8000/docs` (API documentation)

**Expected:** Web interface or API endpoints working

#### 9.2 Test RAG (Slow, Needs LLM)

**Only if you downloaded the LLM model:**

```bash
python scripts/tests/test_rag_compatible.py
```

**Note:** 
- First query: 2-5 minutes (model loading)
- Each query: 10-30+ minutes (CPU inference)
- This is normal for CPU - very slow!

---

## 🔧 Configuration Files

### Files You May Need to Modify:

1. **`.env`** ⚠️ **MUST CREATE**
   - Database credentials
   - API key (if using API)

2. **`config/search_config.json`**
   - Query patterns (Hebrew/English)
   - Field mappings
   - Adjust for your language/domain

3. **`scripts/utils/text_processing.py`**
   - Field weights (which fields are more important)
   - Adjust for your data structure

---

## 📊 Verify Setup

### Check Database:

```sql
-- Connect to database
psql -U postgres -d ai_requests_db

-- Check requests table
SELECT COUNT(*) FROM requests;
-- Should show your row count

-- Check embeddings table
SELECT COUNT(*) FROM request_embeddings;
-- Should show number of chunks (usually 3-5x number of requests)

-- Check pgvector extension
\dx vector
-- Should show: vector | 1.0 | public | ...

-- Exit
\q
```

### Check Python Environment:

```bash
# Check Python version
python --version
# Should be 3.10+

# Check installed packages
pip list | findstr "psycopg2 sentence-transformers torch fastapi"
# Windows: findstr
# Linux/Mac: grep

# Should show all packages installed
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "Module not found" or "No module named X"

**Solution:**
```bash
# Make sure virtual environment is activated
# Windows: .\venv\Scripts\activate.ps1
# Linux/Mac: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 2: "Cannot connect to database" or "Connection refused"

**Solution:**
- Check `.env` file (credentials correct?)
- Verify PostgreSQL is running:
  - Windows: `Get-Service postgresql*`
  - Linux: `sudo systemctl status postgresql`
- Test connection manually:
  - Windows: `psql -U postgres -h localhost -p 5432`
  - Linux: `sudo -u postgres psql`
- Check port number (5432 vs 5433)

### Issue 3: "pgvector extension not found" or "extension does not exist"

**Solution:**
- Install pgvector extension (see Step 3.2)
- Restart PostgreSQL service
- Re-run: `CREATE EXTENSION vector;` in the database
- Check PostgreSQL version compatibility

### Issue 4: "Out of memory" during embedding generation

**Solution:**
- Close other applications
- Process in smaller batches (modify script)
- Use a machine with more RAM (8GB+ recommended)
- Restart computer to clear memory fragmentation

### Issue 5: "Model not found" for RAG

**Solution:**
- Download LLM model (see Step 8)
- Or use retrieval-only mode (`use_llm=False` in API)
- Check model path: `models/llm/mistral-7b-instruct/`

### Issue 6: CSV import fails

**Solution:**
- Check CSV file path
- Verify CSV has headers (column names in first row)
- Check CSV encoding (should be UTF-8)
- Verify database connection (`.env` file)

### Issue 7: "Permission denied" errors

**Solution:**
- Windows: Run PowerShell as Administrator
- Linux: Use `sudo` where needed
- Check file/folder permissions

---

## 📁 Project Structure Overview

```
train_ai_tamar_request/
├── .env                          # ⚠️ CREATE THIS - Database credentials
├── requirements.txt              # Python dependencies
├── README.md                     # Project overview
├── SETUP_GUIDE_FOR_NEW_USER.md   # This file
├── COMPLETE_PROJECT_GUIDE.md     # Main documentation
├── data/
│   └── raw/
│       └── requests.csv          # ⚠️ PLACE YOUR DATA HERE
├── scripts/
│   ├── core/
│   │   ├── generate_embeddings.py    # Generate embeddings
│   │   ├── search.py                 # Search script
│   │   └── rag_query.py              # RAG system
│   ├── helpers/
│   │   └── import_csv_to_postgres.py # Import data
│   └── utils/
│       ├── query_parser.py            # Query parsing
│       └── text_processing.py         # Text processing
├── api/
│   ├── app.py                    # FastAPI server
│   ├── services.py               # Service layer
│   ├── frontend/                 # Web interface
│   └── requirements.txt          # API dependencies
├── config/
│   └── search_config.json        # Query patterns
├── models/
│   └── llm/                      # LLM model (download separately)
└── docs/                         # Documentation
```

---

## 🎯 Quick Start Checklist

Use this checklist to track your progress:

- [ ] **Step 1:** Project folder downloaded/extracted
- [ ] **Step 2:** Python 3.10+ installed
- [ ] **Step 2:** Virtual environment created and activated
- [ ] **Step 2:** Dependencies installed (`pip install -r requirements.txt`)
- [ ] **Step 3:** PostgreSQL installed
- [ ] **Step 3:** pgvector extension installed
- [ ] **Step 3:** Database `ai_requests_db` created
- [ ] **Step 3:** pgvector extension enabled (`CREATE EXTENSION vector;`)
- [ ] **Step 4:** `.env` file created with database credentials
- [ ] **Step 5:** Data CSV prepared (`data/raw/requests.csv`)
- [ ] **Step 6:** Data imported to PostgreSQL
- [ ] **Step 6:** Verified import (checked row count)
- [ ] **Step 7:** Embeddings generated
- [ ] **Step 7:** Verified embeddings (checked count)
- [ ] **Step 8:** (Optional) LLM model downloaded
- [ ] **Step 9:** Search tested and working
- [ ] **Step 9:** (Optional) API tested and working
- [ ] **Step 9:** (Optional) RAG tested and working

---

## 🚀 Running the System

### Option 1: Search Only (Fast, No LLM)

```bash
# Make sure virtual environment is activated
python scripts/core/search.py
```

**Enter queries like:**
- "פניות מאור גלילי"
- "requests from John"
- "פניות מסוג 4"

**Expected:** List of relevant requests with similarity scores

---

### Option 2: API Server (Recommended)

```bash
# Make sure virtual environment is activated
cd api

# Install API dependencies (if not already installed)
pip install -r requirements.txt

# Start server
python -m uvicorn app:app --reload --port 8000
```

**Then:**
- Open browser: `http://localhost:8000` (frontend interface)
- Or API docs: `http://localhost:8000/docs` (Swagger UI)
- Or API endpoint: `http://localhost:8000/api/search` (POST request)

**Expected:** Web interface or API working

**To stop server:** Press `Ctrl+C`

---

### Option 3: RAG (Slow, Needs LLM)

**Only if you downloaded the LLM model:**

```bash
# Make sure virtual environment is activated
python scripts/tests/test_rag_compatible.py
```

**Or via API:**
```bash
# Start API server first (see Option 2)
# Then use RAG endpoint: POST /api/rag/query
```

**Note:** 
- First query: 2-5 minutes (model loading)
- Each query: 10-30+ minutes (CPU inference)
- This is normal for CPU - very slow!

---

## 📝 Next Steps After Setup

1. **Test with your data:**
   - Try different queries
   - Verify results are correct
   - Check if Hebrew/English works

2. **Customize for your project:**
   - Update query patterns in `config/search_config.json`
   - Adjust field mappings (Hebrew → English field names)
   - Modify field weights in `scripts/utils/text_processing.py`

3. **Deploy to server** (if needed):
   - See `api/DEPLOYMENT_GUIDE.md`
   - Set up as Windows service or Linux systemd
   - Configure firewall/network access

4. **Optimize performance:**
   - See `docs/RAG_SPEED_OPTIMIZATION_OPTIONS.md`
   - Consider GPU for faster RAG
   - Or use API-based LLM

---

## 🆘 Getting Help

**If something doesn't work:**

1. **Check error messages carefully:**
   - Python errors show in terminal
   - Database errors show connection issues
   - Import errors show missing packages

2. **Verify each step:**
   - Database connection works? (test with psql)
   - Data imported correctly? (check row count)
   - Embeddings generated? (check embeddings count)
   - Dependencies installed? (check pip list)

3. **Common fixes:**
   - Restart PostgreSQL service
   - Reinstall Python dependencies
   - Check `.env` file format (no quotes, correct values)
   - Verify file paths (use absolute paths if needed)

4. **Documentation:**
   - `COMPLETE_PROJECT_GUIDE.md` - Full project guide
   - `docs/important/` - Essential documentation
   - `api/README.md` - API documentation
   - `api/DEPLOYMENT_GUIDE.md` - Deployment guide

---

## ✅ Success Indicators

**You're ready when:**

- ✅ Database has data (`SELECT COUNT(*) FROM requests;` returns > 0)
- ✅ Embeddings generated (`SELECT COUNT(*) FROM request_embeddings;` returns > 0)
- ✅ Search works (`python scripts/core/search.py` returns results)
- ✅ API works (if using API, server starts without errors)
- ✅ (Optional) RAG works (if model downloaded, generates answers)

---

## 📞 Support & Documentation

**Main Documentation:**
- `COMPLETE_PROJECT_GUIDE.md` - Complete project overview
- `docs/important/` - Essential documentation by topic
- `api/README.md` - API documentation
- `api/DEPLOYMENT_GUIDE.md` - Server deployment

**Common Questions:**
- "How do I change query patterns?" → `config/search_config.json`
- "How do I add more fields?" → `scripts/utils/text_processing.py`
- "How do I deploy to server?" → `api/DEPLOYMENT_GUIDE.md`
- "How does the system work?" → `docs/important/06_SYSTEM_FLOW_AND_ARCHITECTURE.md`
- "What can I configure?" → `docs/important/08_CONFIGURATION_AND_TUNING.md`

---

## 🎉 You're Done!

**Once all steps are complete, you should have:**
- ✅ Working search system
- ✅ Database with embeddings
- ✅ (Optional) RAG system for textual answers
- ✅ (Optional) API server for web interface

**Next:** Start using the system with your data!

**Good luck! 🚀**
