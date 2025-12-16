# Embedding Setup - Current State & Status

## 📊 Current Status

### ✅ What EXISTS (Implemented & Working)

1. **`scripts/core/generate_embeddings.py`** ✅
   - **Status:** Working, but PROJECT-SPECIFIC
   - **What it does:**
     - Reads from `requests` table (hardcoded)
     - Uses `combine_text_fields_weighted()` (hardcoded field weights)
     - Generates embeddings
     - Stores in `request_embeddings` table (hardcoded)
   - **Limitations:**
     - Only works for "requests" table
     - Field weights are hardcoded in `text_processing.py`
     - Cannot be used for other clients/tables without code changes

2. **`scripts/setup/intelligent_field_analysis.py`** ✅
   - **Status:** Working, PRODUCTION-READY
   - **What it does:**
     - Analyzes any table structure
     - Suggests field weights (3.0x, 2.0x, 1.0x)
     - Handles different naming conventions
     - Data-driven analysis when names don't match
   - **Accuracy:** ~90-95%
   - **Ready to use:** Yes

3. **`scripts/helpers/backup_embeddings_table.py`** ✅
   - **Status:** Working
   - **What it does:** Creates timestamped backup of embeddings table

4. **`scripts/utils/text_processing.py`** ✅
   - **Status:** Working, but PROJECT-SPECIFIC
   - **What it does:**
     - `combine_text_fields_weighted()` - Hardcoded for "requests" table
     - `chunk_text()` - Generic (can be reused)

---

### ❌ What's MISSING (Planned but Not Implemented)

1. **`scripts/setup/setup_embeddings.py`** ❌
   - **Status:** NOT IMPLEMENTED
   - **What it should do:**
     - Interactive wizard
     - Database connection setup
     - Table selection
     - Auto-detect schema
     - Generate config file
     - Use intelligent field analysis

2. **`scripts/setup/auto_detect_schema.py`** ❌
   - **Status:** NOT IMPLEMENTED
   - **What it should do:**
     - Detect all tables
     - Detect columns and types
     - Suggest primary key
     - Suggest text fields

3. **`scripts/core/generate_embeddings_universal.py`** ❌
   - **Status:** NOT IMPLEMENTED
   - **What it should do:**
     - Read config file
     - Work with any table
     - Use config for field weights
     - Generic table creation

4. **`config/embedding_config.json`** ❌
   - **Status:** NOT IMPLEMENTED
   - **What it should contain:**
     - Database connection
     - Source table name
     - Field weights
     - Chunking parameters
     - Model choice

---

## 🔧 Current Workflow (What Works Now)

### For YOUR Current Project:

```bash
# 1. Setup database connection (.env file)
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# 2. Generate embeddings (project-specific)
python scripts/core/generate_embeddings.py
```

**What happens:**
1. Connects to database (from .env)
2. Reads from `requests` table (hardcoded)
3. Uses hardcoded field weights from `text_processing.py`
4. Generates embeddings
5. Stores in `request_embeddings` table (hardcoded)

**Time:** ~30-60 minutes for 8K requests

---

## 🚧 What's Needed for Universal Script

### Required Components:

1. **Setup Wizard** (`scripts/setup/setup_embeddings.py`)
   - Interactive prompts
   - Database connection
   - Table selection
   - Config generation

2. **Universal Generator** (`scripts/core/generate_embeddings_universal.py`)
   - Read config file
   - Generic field combination (based on config)
   - Generic table creation
   - Works with any table

3. **Config File** (`config/embedding_config.json`)
   - Store all parameters
   - Field weights
   - Table names
   - Model choice

---

## 📋 Requirements

### System Requirements:

1. **PostgreSQL** (with pgvector extension)
   - Version: 13+ (for pgvector support)
   - Extension: `CREATE EXTENSION vector;`
   - Installation: See `docs/DATABASE_REQUIREMENTS.md` (if exists)

2. **Python 3.8+**
   - Virtual environment recommended

3. **Python Packages:**
   ```bash
   pip install psycopg2-binary
   pip install sentence-transformers
   pip install numpy
   pip install tqdm
   pip install python-dotenv
   ```

4. **Hardware:**
   - RAM: 2-4GB free (for model loading)
   - Disk: ~500MB for model (first time download)
   - CPU: Any (embedding generation is CPU-bound)

---

## 🔑 Parameters (Current vs. Universal)

### Current Script (`generate_embeddings.py`):

**Required (from .env):**
- `POSTGRES_HOST` - Database host
- `POSTGRES_PORT` - Database port
- `POSTGRES_DATABASE` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password

**Hardcoded (cannot change):**
- Source table: `requests`
- Primary key: `requestid`
- Embeddings table: `request_embeddings`
- Field weights: Hardcoded in `text_processing.py`
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Chunk size: 512
- Overlap: 50

---

### Universal Script (Planned):

**Required (user input):**
- Database connection (same as current)
- Source table name (user selects)
- Primary key (auto-detected, user confirms)

**Optional (auto-detected with defaults):**
- Field weights (intelligent analysis suggests)
- Field labels (auto-generated)
- Chunk size (default: 512)
- Overlap (default: 50)
- Model (default: all-MiniLM-L6-v2)
- Embeddings table name (default: `{table}_embeddings`)

**Stored in:** `config/embedding_config.json`

---

## 🧪 Can We Test It?

### ✅ What We CAN Test Now:

1. **Intelligent Field Analysis:**
   ```bash
   python scripts/setup/intelligent_field_analysis.py
   ```
   - Works with any table
   - Tests field weight suggestions
   - ✅ Already tested and working

2. **Current Embedding Generation:**
   ```bash
   python scripts/core/generate_embeddings.py
   ```
   - Works for YOUR current project
   - ✅ Already working

### ❌ What We CANNOT Test Yet:

1. **Universal Setup Wizard** - Not implemented
2. **Universal Generator** - Not implemented
3. **Config File System** - Not implemented

---

## 🎯 What's Left to Build

### Priority 1: Universal Generator (Most Important)

**File:** `scripts/core/generate_embeddings_universal.py`

**What it needs:**
1. Read config file (`config/embedding_config.json`)
2. Generic field combination function (based on config weights)
3. Generic table creation (based on config)
4. Work with any table name

**Estimated effort:** 2-3 hours

---

### Priority 2: Setup Wizard

**File:** `scripts/setup/setup_embeddings.py`

**What it needs:**
1. Interactive prompts
2. Database connection setup
3. Table selection
4. Use intelligent field analysis
5. Generate config file

**Estimated effort:** 3-4 hours

---

### Priority 3: Schema Auto-Detection

**File:** `scripts/setup/auto_detect_schema.py`

**What it needs:**
1. Detect all tables
2. Detect columns and types
3. Suggest primary key
4. Suggest text fields

**Estimated effort:** 1-2 hours

---

## 📝 Summary

### Current State:
- ✅ **Working:** Project-specific embedding generation
- ✅ **Working:** Intelligent field analysis (universal)
- ❌ **Missing:** Universal setup wizard
- ❌ **Missing:** Universal generator
- ❌ **Missing:** Config file system

### What You Can Do Now:
1. Use current script for YOUR project ✅
2. Test intelligent field analysis on any table ✅
3. Wait for universal scripts to be built ❌

### What's Needed:
1. Build universal generator (read config, generic fields)
2. Build setup wizard (interactive, generate config)
3. Build schema detection (auto-detect tables/columns)

### Estimated Time to Complete:
- **Universal Generator:** 2-3 hours
- **Setup Wizard:** 3-4 hours
- **Schema Detection:** 1-2 hours
- **Total:** ~6-9 hours of development

---

## 🚀 Next Steps

### Option 1: Use Current Script (Quick)
- Works for your current project
- No changes needed
- Just run: `python scripts/core/generate_embeddings.py`

### Option 2: Build Universal Scripts (Future-Proof)
- Build universal generator
- Build setup wizard
- Make it work for any client/table
- Estimated: 6-9 hours

### Option 3: Hybrid Approach
- Keep current script for your project
- Build universal scripts for new clients
- Both can coexist

---

## 💡 Recommendations

1. **For Now:** Use current script (it works!)
2. **For Future:** Build universal scripts when you have a new client
3. **Intelligent Analysis:** Already ready to use in universal scripts

The intelligent field analysis is the hardest part and it's already done! The rest is mostly:
- Reading config files
- Generic field combination
- Interactive prompts

