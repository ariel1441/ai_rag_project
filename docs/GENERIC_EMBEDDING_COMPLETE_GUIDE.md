# Generic Embedding Setup - Complete Guide

## 📋 Table of Contents

1. [What It Does](#what-it-does)
2. [Before You Start](#before-you-start)
3. [Step-by-Step Process](#step-by-step-process)
4. [What Happens Automatically](#what-happens-automatically)
5. [What User Enters](#what-user-enters)
6. [What Gets Downloaded](#what-gets-downloaded)
7. [CSV Import Option](#csv-import-option)
8. [Complete Flow Diagram](#complete-flow-diagram)

---

## 🎯 What It Does

The generic embedding setup converts **any database table** into **searchable embeddings** that enable semantic search (finding by meaning, not just keywords).

**Input:** Database table or CSV file  
**Output:** Embeddings table with vector representations  
**Result:** Can search for similar content by meaning

---

## 📋 Before You Start

### Prerequisites (One-Time Setup):

#### 1. Install PostgreSQL
- **Download:** https://www.postgresql.org/download/
- **Or Docker:** `docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=password pgvector/pgvector:pg16`
- **Time:** 10-30 minutes
- **What it does:** Provides database server

#### 2. Enable pgvector Extension
```sql
CREATE EXTENSION vector;
```
- **Time:** 1 minute
- **What it does:** Adds vector data type support
- **Where:** Run in your PostgreSQL database

#### 3. Install Python Packages
```bash
pip install psycopg2-binary sentence-transformers numpy tqdm python-dotenv
```
- **Time:** 2-5 minutes
- **What it downloads:**
  - `psycopg2-binary` (~5MB) - PostgreSQL driver
  - `sentence-transformers` (~50MB base) - Embedding framework
  - `numpy` (~15MB) - Numerical computing
  - `tqdm` (~1MB) - Progress bars
  - `python-dotenv` (~1MB) - Environment variables
- **Total:** ~72MB

#### 4. Prepare Data Source
**Option A: Data in PostgreSQL**
- Table already exists
- Just need table name

**Option B: Data in CSV**
- Export from SQL Server/MySQL/etc.
- Save as CSV file
- Script will import it

#### 5. Create .env File (Optional but Recommended)
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=your_database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```
- **Time:** 1 minute
- **What it does:** Stores credentials (not hardcoded)

---

## 🚀 Step-by-Step Process

### STEP 1: Run Setup Wizard

**Command:**
```bash
python scripts/setup/setup_embeddings.py
```

#### What User Enters:

1. **Database Connection** (if not in .env):
   - Host: `localhost` (default)
   - Port: `5433` (default)
   - Database: `your_database`
   - User: `postgres` (default)
   - Password: `your_password`

2. **Data Source Choice:**
   - **Option A:** Import CSV file
     - CSV file path: `C:\data\export.csv`
     - Table name: `imported_data`
   - **Option B:** Use existing table
     - Select from list: `1` (for first table)

3. **Primary Key:**
   - Accept suggested: `yes` (default)
   - OR enter custom: `id`

4. **Chunking Parameters:**
   - Chunk size: `512` (default)
   - Overlap: `50` (default)

5. **Model Choice:**
   - Option 1: `all-MiniLM-L6-v2` (384 dims, fast) - **Recommended**
   - Option 2: `all-mpnet-base-v2` (768 dims, slower, better)
   - Option 3: Custom model name

#### What Happens Automatically:

1. ✅ **Connects to Database**
   - Tests connection
   - Verifies pgvector extension

2. ✅ **CSV Import (if chosen):**
   - Detects CSV structure (columns, types, delimiter)
   - Creates PostgreSQL table
   - Imports all data
   - Reports row count

3. ✅ **Detects All Tables** (if using existing):
   - Queries `information_schema.tables`
   - Lists all tables with row counts

4. ✅ **Detects Table Schema:**
   - Gets all columns and types
   - Suggests primary key (patterns: `_id`, `id`, `{table}id`)
   - Suggests text fields (excludes IDs, dates, booleans)

5. ✅ **Runs Intelligent Field Analysis:**
   - For each column:
     - Analyzes column name (patterns: name, desc, text, etc.)
     - Analyzes sample data (1000 rows):
       - Coverage (% non-null)
       - Uniqueness (% unique values)
       - Diversity (distribution)
       - Average text length
     - Combines analysis → suggests weight (3.0x, 2.0x, 1.0x)
   - Returns weight suggestions

6. ✅ **Generates Configuration File:**
   - Creates `config/embedding_config.json`
   - Includes: database, source, fields, chunking, embedding, output

#### What Gets Downloaded:
- **Nothing** (all analysis is local)

#### Time:
- **2-5 minutes**

#### Output:
- `config/embedding_config.json` file

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

#### What User Enters:
- **Nothing** (all from config file)
- Optional: Confirmation to replace existing embeddings (if table exists)

#### What Happens Automatically:

##### 3.1: Load Configuration
- ✅ Reads `config/embedding_config.json`
- ✅ Gets database connection info
- ✅ Gets source table name
- ✅ Gets field weights
- ✅ Gets chunking parameters
- ✅ Gets model choice
- **Time:** <1 second

##### 3.2: Connect to Database
- ✅ Connects using config credentials
- ✅ Verifies connection
- **Time:** <1 second

##### 3.3: Load Embedding Model
- ✅ **Downloads model (first time only):**
  - `all-MiniLM-L6-v2`: ~90MB
  - `all-mpnet-base-v2`: ~420MB
- ✅ Loads model into memory
- ✅ Caches model locally (`~/.cache/torch/sentence_transformers/`)
- **Time:** 30-60 seconds (first time), 5-10 seconds (subsequent)

##### 3.4: Load Source Data
- ✅ Executes SQL: `SELECT * FROM {table} ORDER BY {primary_key}`
- ✅ Fetches all rows
- ✅ Converts to Python dictionaries
- **Time:** 1-5 minutes (depends on table size)

##### 3.5: Create Embeddings Table
- ✅ Creates table: `{source_table}_embeddings`
- ✅ Columns:
  - `id` (serial primary key)
  - `{primary_key}` (foreign key to source table)
  - `chunk_index` (which chunk of the text)
  - `text_chunk` (the actual text)
  - `embedding` (vector of numbers, e.g., 384 or 768 numbers)
  - `metadata` (JSON with extra info)
  - `created_at` (timestamp)
- ✅ Creates vector index (IVFFlat) for fast similarity search
- ✅ Creates index on primary key for joins
- **Time:** 1-2 seconds

##### 3.6: Prepare Text Documents
- ✅ For each row in source table:
  - Gets all field values
  - Filters by config (excludes excluded fields)
  - Combines fields with labels:
    - **3.0x fields:** Repeated 3 times
    - **2.0x fields:** Repeated 2 times
    - **1.0x fields:** Included once
  - Format: `"Field Label: value | Field Label: value | ..."`
  - Chunks if text > 512 chars:
    - Splits into 512-char pieces
    - 50-char overlap between chunks
    - One row can become multiple chunks
- ✅ Creates list of document chunks
- **Time:** 1-5 minutes (depends on table size and text length)

##### 3.7: Generate Embeddings
- ✅ For each text chunk:
  - Converts text to vector of numbers
  - Example: "Hello world" → `[0.123, -0.456, 0.789, ...]` (384 or 768 numbers)
  - Uses sentence-transformers model
- ✅ Processes in batches (32 at a time by default)
- ✅ Normalizes vectors (length = 1.0)
- ✅ Shows progress bar
- **Time:** 30-60 minutes per 8K rows (depends on CPU)
- **What it does:** Converts text → numbers (vectors) that represent meaning

##### 3.8: Store Embeddings
- ✅ For each embedding:
  - Converts vector to string: `"[0.123, -0.456, ...]"`
  - Inserts into database
  - PostgreSQL converts string → vector type
- ✅ Processes in batches (100 at a time)
- ✅ Commits after each batch
- **Time:** 2-5 minutes (depends on number of chunks)

##### 3.9: Verify
- ✅ Counts embeddings in database
- ✅ Verifies count matches expected
- **Time:** <1 second

#### What Gets Downloaded:
- **Embedding model (first time only):**
  - `all-MiniLM-L6-v2`: ~90MB
  - `all-mpnet-base-v2`: ~420MB
- **Location:** `~/.cache/torch/sentence_transformers/`
- **Cached:** Yes (reused for future runs)

#### Time:
- **35-75 minutes total** (for 8K rows)
  - Load model: 30-60 seconds (first time), 5-10 seconds (subsequent)
  - Load data: 1-5 minutes
  - Prepare documents: 1-5 minutes
  - Generate embeddings: 30-60 minutes (CPU-bound, longest step)
  - Store embeddings: 2-5 minutes

#### Output:
- Embeddings table in PostgreSQL with vector embeddings
- Ready for semantic search

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
  - **Recommended for most cases**
- `all-mpnet-base-v2`: ~420MB
  - 768 dimensions
  - Slower, better quality
  - Use for higher accuracy needs
- **Location:** `~/.cache/torch/sentence_transformers/`
- **Cached:** Yes (reused for future runs)

**Total Download (First Time):** ~150-550MB depending on model choice

---

## 📊 CSV Import Option

### How It Works:

**Option in Setup Wizard:**
1. User chooses "Import CSV file"
2. User enters CSV file path
3. User enters table name
4. Script automatically:
   - Detects CSV structure (columns, types, delimiter)
   - Creates PostgreSQL table
   - Imports all data
   - Continues with embedding setup

### CSV Import Details:

**What Happens Automatically:**
1. ✅ Reads CSV header row
2. ✅ Detects delimiter (comma, semicolon, tab)
3. ✅ Detects column types (integer, numeric, text)
4. ✅ Cleans column names (spaces → underscores)
5. ✅ Creates PostgreSQL table
6. ✅ Imports all rows (batches of 1000)
7. ✅ Reports results

**CSV Requirements:**
- Headers in first row
- UTF-8 encoding
- Comma, semicolon, or tab delimiter

**Standalone Import:**
```bash
python scripts/helpers/import_csv_to_postgres.py data.csv my_table
```

---

## 🔄 Complete Flow Diagram

```
BEFORE START
├── Install PostgreSQL + pgvector
├── Install Python packages
├── Prepare data (PostgreSQL table OR CSV file)
└── Create .env file (optional)

SETUP WIZARD (Step 1)
├── User enters: Database connection
├── User chooses: CSV import OR existing table
│   ├── If CSV: User enters CSV path + table name
│   │   └── Auto: Imports CSV to PostgreSQL
│   └── If existing: User selects from list
├── Auto: Detects schema
├── Auto: Runs intelligent field analysis
├── User confirms: Primary key
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
│   ├── Combines fields (based on config weights)
│   └── Chunks long text
├── Auto: Generates embeddings (LONG STEP - 30-60 min)
├── Auto: Stores embeddings
└── Auto: Verifies results

RESULT
└── Embeddings table ready for semantic search!
```

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
- Generate embeddings: 30-60 minutes (CPU-bound, longest step)
- Store embeddings: 2-5 minutes
- **Total:** 35-75 minutes

**Grand Total:** ~1-2 hours for complete setup + generation

---

## 🎯 What the Script Does in General

### High-Level Overview:

1. **Takes structured data** (database table or CSV)
2. **Combines text fields** into searchable text (with weighting)
3. **Chunks long text** into manageable pieces
4. **Converts text to numbers** (embeddings/vectors) using AI model
5. **Stores vectors in database** with vector index
6. **Enables semantic search** (find similar meaning, not just keywords)

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
   - "פניות מאלינור" → `[0.123, -0.456, 0.789, ...]` (384 numbers)
   - Similar texts → Similar vectors

2. **Vector Similarity:**
   - Compare vectors using cosine similarity
   - Similar vectors = similar meaning
   - Fast with vector index (IVFFlat)

3. **Search:**
   - User query → Embedding → Find similar vectors → Return results

---

## ✅ Summary

### What User Does:
1. **Before:** Install prerequisites (one-time)
2. **Step 1:** Run setup wizard (enter connection, select table, confirm settings)
3. **Step 2:** Run generator (wait for embeddings)

### What Scripts Do Automatically:
- ✅ Detect schema
- ✅ Analyze fields
- ✅ Suggest weights
- ✅ Generate config
- ✅ Download model (first time)
- ✅ Load data
- ✅ Create tables
- ✅ Combine fields
- ✅ Chunk text
- ✅ Generate embeddings
- ✅ Store in database

### What Gets Downloaded:
- Python packages (~72MB, one-time)
- Embedding model (~90-420MB, first time per model)

### Total Time:
- Setup: 15-40 minutes
- Generation: 35-75 minutes (for 8K rows)
- **Total: ~1-2 hours**

### Result:
- Embeddings table ready for semantic search
- Can find similar content by meaning
- Works with any table structure
- Supports CSV import from any database

---

## 🎯 Key Features

✅ **Universal:** Works with any table structure  
✅ **Intelligent:** Auto-suggests field weights  
✅ **Flexible:** Supports CSV import  
✅ **Configurable:** All parameters in config file  
✅ **Efficient:** Batch processing, progress bars  
✅ **Safe:** Doesn't modify source data  
✅ **Separate:** Doesn't touch project-specific scripts  

