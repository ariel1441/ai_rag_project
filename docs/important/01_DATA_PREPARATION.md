# Data Preparation - Complete Guide

**Everything about data export, import, and database setup before embedding generation**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Data Export from SQL Server](#data-export-from-sql-server)
3. [PostgreSQL Setup](#postgresql-setup)
4. [Data Import](#data-import)
5. [Database Schema](#database-schema)
6. [Data Validation](#data-validation)
7. [Troubleshooting](#troubleshooting)

---

## Overview

**Goal:** Export data from production SQL Server to isolated PostgreSQL database for AI processing.

**What We Did:**
- ✅ Exported Requests table from SQL Server to CSV
- ✅ Created isolated PostgreSQL database (`ai_requests_db`)
- ✅ Imported 8,195 requests with all 83 columns
- ✅ Used staging table approach for safe import
- ✅ Environment variables for credentials (.env file)

**Result:** 8,195 requests successfully imported and isolated

---

## Data Export from SQL Server

### Export Process

**Step 1: Export to CSV**
- Export the `Requests` table from SQL Server
- Save as CSV file (e.g., `data/raw/request.csv`)
- Ensure UTF-8 encoding for Hebrew support

**Step 2: Verify Export**
- Check row count matches source
- Verify all columns exported
- Check Hebrew text displays correctly

**Key File:** `data/raw/request.csv`

---

## PostgreSQL Setup

### Installation

**Windows:**
1. Download PostgreSQL 18 from official website
2. Install with default settings
3. Note the port (default: 5432, we use 5433)
4. Set postgres user password

**Linux:**
```bash
sudo apt-get install postgresql-18
```

### Create Database

```sql
CREATE DATABASE ai_requests_db;
```

### Install pgvector Extension

**Windows:**
- Download pgvector from GitHub
- Compile and install manually
- Or use pre-built binaries if available

**Linux:**
```bash
# Install pgvector extension
# Follow pgvector installation guide
```

**Enable Extension:**
```sql
\c ai_requests_db
CREATE EXTENSION vector;
```

---

## Data Import

### Import Script

**File:** `scripts/helpers/import_csv_to_postgres.py`

**How it works:**
1. Reads CSV file
2. Creates staging table
3. Imports data to staging
4. Validates data
5. Copies to main `requests` table
6. Cleans up staging table

**Usage:**
```bash
python scripts/helpers/import_csv_to_postgres.py
```

**Features:**
- Safe import (staging table approach)
- Handles encoding issues
- Validates data types
- Reports import statistics

### Environment Variables

**File:** `.env`

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
```

**Security:** Never commit `.env` to git!

---

## Database Schema

### Requests Table

**Structure:**
- 8,195 rows
- 83 columns (all TEXT type for simplicity)
- Primary key: `requestid`

**Key Columns:**
- `requestid` - Unique identifier
- `projectname` - Project name (Hebrew)
- `updatedby` - Person who updated (Hebrew)
- `createdby` - Person who created (Hebrew)
- `requesttypeid` - Type ID (references lookup table)
- `requeststatusid` - Status ID (references lookup table)
- ... 77 more columns

**Note:** All columns are TEXT type to simplify import and handle any data format.

### Request Embeddings Table

**Created later** (during embedding generation):
- `requestid` - Foreign key to requests
- `chunk_index` - Chunk number (0, 1, 2, ...)
- `text_chunk` - The actual text chunk
- `embedding` - Vector(384) - the embedding
- `metadata` - JSON with extra info

**Indexes:**
- Vector index on `embedding` (for fast similarity search)
- Foreign key index on `requestid`

---

## Data Validation

### After Import

**Check row count:**
```sql
SELECT COUNT(*) FROM requests;
-- Should match: 8,195
```

**Check columns:**
```sql
SELECT COUNT(*) FROM information_schema.columns 
WHERE table_name = 'requests';
-- Should be: 83
```

**Check Hebrew encoding:**
```sql
SELECT projectname, updatedby FROM requests LIMIT 5;
-- Should display Hebrew correctly
```

**Check for NULLs:**
```sql
SELECT 
    COUNT(*) as total,
    COUNT(projectname) as has_projectname,
    COUNT(updatedby) as has_updatedby
FROM requests;
```

---

## Troubleshooting

### Import Errors

**Problem:** Encoding errors (Hebrew text corrupted)
**Solution:** Ensure CSV is UTF-8 encoded

**Problem:** Column count mismatch
**Solution:** Check CSV has all 83 columns

**Problem:** Data type errors
**Solution:** All columns are TEXT, should handle any format

### Database Connection

**Problem:** Connection refused
**Solution:**
```powershell
# Windows: Start PostgreSQL service
Start-Service postgresql-x64-18

# Verify it's running
Get-Service postgresql-x64-18
```

**Problem:** Wrong password
**Solution:** Check `.env` file, verify password

**Problem:** Port conflict
**Solution:** Check port in `.env` matches PostgreSQL port

---

## Next Steps

After data import:
1. ✅ Data imported successfully
2. → **Next:** Generate embeddings (see `02_EMBEDDING_SYSTEM.md`)
3. → **Next:** Set up search (see `03_SEARCH_SYSTEM.md`)

---

## Key Files

- `scripts/helpers/import_csv_to_postgres.py` - Import script
- `.env` - Database credentials
- `data/raw/request.csv` - Source CSV file
- `sql/` - SQL scripts (if any)

---

**Last Updated:** Current Session  
**Status:** Complete and tested

