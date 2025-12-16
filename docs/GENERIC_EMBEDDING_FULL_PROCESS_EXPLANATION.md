# Generic Embedding Setup - Complete Process Explanation

## 🎯 Overview

This document explains **every step** of the generic embedding setup process:
- What happens automatically
- What the user needs to enter
- What the user needs to do before
- What gets downloaded
- What the script does in general

---

## 📋 Before You Start

### What User Needs to Do BEFORE Running Scripts:

1. **Install PostgreSQL** (if not already installed)
   - Download from: https://www.postgresql.org/download/
   - Or use Docker: `docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=password pgvector/pgvector:pg16`
   - **Time:** 10-30 minutes

2. **Enable pgvector Extension** (one-time per database)
   ```sql
   CREATE EXTENSION vector;
   ```
   - **Time:** 1 minute
   - **What it does:** Adds vector data type support to PostgreSQL

3. **Install Python Packages** (one-time)
   ```bash
   pip install psycopg2-binary sentence-transformers numpy tqdm python-dotenv
   ```
   - **Time:** 2-5 minutes
   - **What it downloads:**
     - `psycopg2-binary` - PostgreSQL driver (~5MB)
     - `sentence-transformers` - Embedding models (~50MB base, +500MB for models)
     - `numpy` - Numerical computing (~15MB)
     - `tqdm` - Progress bars (~1MB)
     - `python-dotenv` - Environment variables (~1MB)

4. **Prepare Data Source** (choose one):
   - **Option A:** Data already in PostgreSQL
     - Just need table name
   - **Option B:** Data in CSV file
     - Export from SQL Server/MySQL/etc.
     - Save as CSV file
     - Script will import it

5. **Create .env File** (optional, but recommended)
   ```
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5433
   POSTGRES_DATABASE=your_database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   ```
   - **Time:** 1 minute
   - **What it does:** Stores database credentials (not hardcoded in scripts)

---

## 🚀 Step-by-Step Process

### STEP 1: Run Setup Wizard

**Command:**
```bash
python scripts/setup/setup_embeddings.py
```

**What User Enters:**
1. Database connection (if not in .env):
   - Host (default: localhost)
   - Port (default: 5433)
   - Database name
   - User (default: postgres)
   - Password

2. Data source choice:
   - **Option A:** Import CSV file
     - CSV file path
     - Table name for imported data
   - **Option B:** Use existing table
     - Select from list of tables

3. Primary key confirmation:
   - Accept suggested primary key
   - OR enter custom primary key

4. Chunking parameters:
   - Chunk size (default: 512)
   - Overlap (default: 50)

5. Model choice:
   - Option 1: all-MiniLM-L6-v2 (384 dims, fast)
   - Option 2: all-mpnet-base-v2 (768 dims, slower, better)
   - Option 3: Custom model name

**What Happens Automatically:**
1. ✅ Connects to database
2. ✅ Detects all tables (if using existing table)
3. ✅ Detects table schema (columns, types)
4. ✅ Suggests primary key (based on common patterns)
5. ✅ Suggests text fields (excludes IDs, dates, booleans)
6. ✅ Runs intelligent field analysis:
   - Analyzes column names (patterns)
   - Analyzes sample data (coverage, uniqueness, diversity)
   - Suggests field weights (3.0x, 2.0x, 1.0x)
7. ✅ Generates configuration file (`config/embedding_config.json`)

**What Gets Downloaded:**
- Nothing (all analysis is done locally)

**Time:** 2-5 minutes

**Output:** `config/embedding_config.json` file

---

### STEP 2: (Optional) Review Configuration

**What User Can Do:**
- Edit `config/embedding_config.json`
- Adjust field weights
- Change chunking parameters
- Change model choice

**What Happens Automatically:**
- Nothing (just file editing)

**Time:** 0-10 minutes (optional)

---

### STEP 3: Generate Embeddings

**Command:**
```bash
python scripts/core/generate_embeddings_universal.py
```

**What User Enters:**
- Nothing (all from config file)
- Optional: Confirmation to replace existing embeddings (if table exists)

**What Happens Automatically:**

#### 3.1: Load Configuration
- ✅ Reads `config/embedding_config.json`
- ✅ Gets database connection info
- ✅ Gets source table name
- ✅ Gets field weights
- ✅ Gets chunking parameters
- ✅ Gets model choice

#### 3.2: Connect to Database
- ✅ Connects using config credentials
- ✅ Verifies connection

#### 3.3: Load Embedding Model
- ✅ Downloads model (first time only):
  - `all-MiniLM-L6-v2`: ~90MB
  - `all-mpnet-base-v2`: ~420MB
- ✅ Loads model into memory
- **Time:** 30-60 seconds (first time), 5-10 seconds (subsequent)

#### 3.4: Load Source Data
- ✅ Executes SQL: `SELECT * FROM {table} ORDER BY {primary_key}`
- ✅ Fetches all rows
- ✅ Converts to Python dictionaries
- **Time:** 1-5 minutes (depends on table size)

#### 3.5: Create Embeddings Table
- ✅ Creates table: `{source_table}_embeddings`
- ✅ Columns:
  - `id` (serial primary key)
  - `{primary_key}` (foreign key to source table)
  - `chunk_index` (which chunk of the text)
  - `text_chunk` (the actual text)
  - `embedding` (vector of numbers)
  - `metadata` (JSON with extra info)
  - `created_at` (timestamp)
- ✅ Creates vector index (for fast similarity search)
- ✅ Creates index on primary key (for joins)
- **Time:** 1-2 seconds

#### 3.6: Prepare Text Documents
- ✅ For each row in source table:
  - Combines all text fields based on config weights
  - Repeats fields based on weight (3.0x = 3 times, 2.0x = 2 times, 1.0x = 1 time)
  - Formats as: `"Field Label: value | Field Label: value | ..."`
  - Chunks long text (splits into pieces of 512 chars with 50 char overlap)
- ✅ Creates list of document chunks
- **Time:** 1-5 minutes (depends on table size and text length)

#### 3.7: Generate Embeddings
- ✅ For each text chunk:
  - Converts text to vector of numbers (384 or 768 numbers)
  - Uses sentence-transformers model
- ✅ Processes in batches (32 at a time by default)
- ✅ Shows progress bar
- **Time:** 30-60 minutes per 8K rows (depends on CPU)
- **What it does:** Converts text → numbers (vectors) that represent meaning

#### 3.8: Store Embeddings
- ✅ Inserts embeddings into database
- ✅ Processes in batches (100 at a time)
- ✅ Commits after each batch
- **Time:** 2-5 minutes (depends on number of chunks)

#### 3.9: Verify
- ✅ Counts embeddings in database
- ✅ Verifies count matches expected
- **Time:** 1 second

**What Gets Downloaded:**
- Embedding model (first time only):
  - `all-MiniLM-L6-v2`: ~90MB
  - `all-mpnet-base-v2`: ~420MB
- Stored in: `~/.cache/torch/sentence_transformers/`

**Time:** 30-60 minutes total (for 8K rows)

**Output:** Embeddings table in PostgreSQL with vector embeddings

---

## 📊 Complete Flow Diagram

```
USER PREPARATION
├── Install PostgreSQL + pgvector
├── Install Python packages
├── Prepare data (PostgreSQL table OR CSV file)
└── Create .env file (optional)

SETUP WIZARD (Step 1)
├── User enters: Database connection
├── User chooses: CSV import OR existing table
├── User confirms: Primary key
├── Auto: Detects schema
├── Auto: Runs intelligent field analysis
├── User enters: Chunking parameters
├── User enters: Model choice
└── Auto: Generates config file

(OPTIONAL) REVIEW CONFIG
└── User edits: config/embedding_config.json

GENERATE EMBEDDINGS (Step 2)
├── Auto: Loads config
├── Auto: Connects to database
├── Auto: Downloads model (first time)
├── Auto: Loads model
├── Auto: Loads source data
├── Auto: Creates embeddings table
├── Auto: Prepares text documents
├── Auto: Generates embeddings (LONG STEP)
├── Auto: Stores embeddings
└── Auto: Verifies results

RESULT
└── Embeddings table ready for semantic search!
```

---

## 🔍 Detailed Explanation of Each Step

### Setup Wizard - What It Does:

**1. Database Connection:**
- Checks `.env` file first
- If not found, asks user
- Tests connection
- Stores in config

**2. Table Selection:**
- **Option A (CSV):**
  - Reads CSV file
  - Detects columns and types
  - Creates PostgreSQL table
  - Imports all data
  - Returns table name
- **Option B (Existing):**
  - Queries database for all tables
  - Shows list with row counts
  - User selects one

**3. Schema Detection:**
- Queries `information_schema.columns`
- Gets all columns and types
- Suggests primary key (patterns: `_id`, `id`, `{table}id`)
- Suggests text fields (excludes IDs, dates, booleans)

**4. Intelligent Field Analysis:**
- For each column:
  - Analyzes column name (patterns: name, desc, text, etc.)
  - Analyzes sample data (1000 rows):
    - Coverage (% non-null)
    - Uniqueness (% unique values)
    - Diversity (how evenly distributed)
    - Average text length
  - Combines analysis → suggests weight (3.0x, 2.0x, 1.0x)
- Returns weight suggestions

**5. Config Generation:**
- Combines all information
- Creates JSON config file
- Includes: database, source, fields, chunking, embedding, output

---

### Universal Generator - What It Does:

**1. Load Configuration:**
- Reads JSON file
- Validates structure
- Replaces password placeholder with actual password from .env

**2. Connect to Database:**
- Uses psycopg2 to connect
- Tests connection
- Gets cursor for queries

**3. Load Model:**
- Downloads from Hugging Face (first time)
- Caches locally (`~/.cache/torch/sentence_transformers/`)
- Loads into memory
- Model converts text → vectors

**4. Load Source Data:**
- Executes: `SELECT * FROM {table} ORDER BY {primary_key}`
- Fetches all rows
- Converts to Python dicts (one per row)

**5. Create Embeddings Table:**
- Drops existing table (if exists)
- Creates new table with:
  - `id` (auto-increment)
  - `{primary_key}` (links to source)
  - `chunk_index` (which chunk)
  - `text_chunk` (the text)
  - `embedding` (vector of numbers)
  - `metadata` (JSON)
- Creates vector index (IVFFlat) for fast similarity search
- Creates index on primary key for joins

**6. Prepare Text Documents:**
- For each row:
  - Gets all field values
  - Filters by config (excludes excluded fields)
  - Combines fields with labels:
    - 3.0x fields: repeated 3 times
    - 2.0x fields: repeated 2 times
    - 1.0x fields: included once
  - Format: `"Field Label: value | Field Label: value | ..."`
  - Chunks if text > 512 chars:
    - Splits into 512-char pieces
    - 50-char overlap between chunks
    - One row can become multiple chunks

**7. Generate Embeddings:**
- For each text chunk:
  - Model.encode(text) → vector of numbers
  - Example: "Hello world" → [0.123, -0.456, 0.789, ...] (384 or 768 numbers)
- Processes in batches (32 at a time)
- Normalizes vectors (length = 1.0)
- Returns numpy array

**8. Store Embeddings:**
- For each embedding:
  - Converts vector to string: `"[0.123, -0.456, ...]"`
  - Inserts into database
  - PostgreSQL converts string → vector type
- Processes in batches (100 at a time)
- Commits after each batch

**9. Verify:**
- Counts rows in embeddings table
- Compares with expected count
- Reports success

---

## 📥 What Gets Downloaded

### Python Packages (One-Time):
- `psycopg2-binary`: ~5MB
- `sentence-transformers`: ~50MB base
- `numpy`: ~15MB
- `tqdm`: ~1MB
- `python-dotenv`: ~1MB
- **Total:** ~72MB

### Embedding Models (First Time Per Model):
- `all-MiniLM-L6-v2`: ~90MB
  - 384 dimensions
  - Fast, good quality
  - Recommended for most cases
- `all-mpnet-base-v2`: ~420MB
  - 768 dimensions
  - Slower, better quality
  - Use for higher accuracy needs
- **Location:** `~/.cache/torch/sentence_transformers/`
- **Cached:** Yes (reused for future runs)

**Total Download (First Time):** ~150-550MB depending on model choice

---

## ⏱️ Time Estimates

### Setup Phase:
- Install PostgreSQL: 10-30 minutes
- Install packages: 2-5 minutes
- Setup wizard: 2-5 minutes
- **Total:** 15-40 minutes

### Generation Phase (8K rows):
- Load model: 30-60 seconds (first time), 5-10 seconds (subsequent)
- Load data: 1-5 minutes
- Prepare documents: 1-5 minutes
- Generate embeddings: 30-60 minutes (CPU-bound)
- Store embeddings: 2-5 minutes
- **Total:** 35-75 minutes

**Grand Total:** ~1-2 hours for complete setup + generation

---

## 🎯 What the Script Does in General

### High-Level Overview:

1. **Takes structured data** (database table or CSV)
2. **Combines text fields** into searchable text
3. **Converts text to numbers** (embeddings/vectors)
4. **Stores vectors in database** with vector index
5. **Enables semantic search** (find similar meaning, not just keywords)

### Why Embeddings?

**Traditional Search:**
- "Find requests with 'אלינור'"
- Only finds exact matches
- Misses: "אלינור בן עקיבא", "אלינור גלילי", etc.

**Semantic Search (with Embeddings):**
- "Find requests about אלינור"
- Finds all variations
- Finds similar names
- Finds related content
- Understands meaning, not just words

### How It Works:

1. **Text → Vector:**
   - "פניות מאלינור" → [0.123, -0.456, 0.789, ...]
   - Similar texts → Similar vectors

2. **Vector Similarity:**
   - Compare vectors using cosine similarity
   - Similar vectors = similar meaning
   - Fast with vector index

3. **Search:**
   - User query → Embedding → Find similar vectors → Return results

---

## ✅ Summary

**What User Does:**
- Install prerequisites (one-time)
- Run setup wizard (enter connection, select table, confirm settings)
- Run generator (wait for embeddings)

**What Scripts Do Automatically:**
- Detect schema
- Analyze fields
- Suggest weights
- Generate config
- Download model (first time)
- Load data
- Create tables
- Combine fields
- Chunk text
- Generate embeddings
- Store in database

**What Gets Downloaded:**
- Python packages (~72MB, one-time)
- Embedding model (~90-420MB, first time per model)

**Total Time:**
- Setup: 15-40 minutes
- Generation: 35-75 minutes (for 8K rows)
- **Total: ~1-2 hours**

**Result:**
- Embeddings table ready for semantic search
- Can find similar content by meaning
- Works with any table structure

