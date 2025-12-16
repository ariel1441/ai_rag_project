# CSV Import Support - Generic Embedding Setup

## 🎯 Overview

The generic embedding setup now supports **CSV import** as a data source option. This allows users to:
- Export data from SQL Server, MySQL, Oracle, or any database
- Import CSV to PostgreSQL
- Generate embeddings from the imported data

---

## 📋 CSV Import Process

### Step 1: Export Data from Source Database

**For SQL Server:**
```sql
-- Export to CSV
bcp "SELECT * FROM your_table" queryout "data.csv" -c -t, -S server_name -d database_name -U username -P password
```

**For MySQL:**
```sql
-- Export to CSV
SELECT * FROM your_table
INTO OUTFILE 'data.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

**For Any Database:**
- Use database export tool
- Export as CSV with headers
- Save file locally

---

### Step 2: Run Setup Wizard

**Command:**
```bash
python scripts/setup/setup_embeddings.py
```

**When asked for table selection:**
1. Choose "Import CSV file" option
2. Enter CSV file path
3. Enter table name for imported data
4. Script automatically:
   - Detects CSV structure (columns, types)
   - Creates PostgreSQL table
   - Imports all data
   - Continues with embedding setup

---

## 🔧 How CSV Import Works

### Automatic Detection:

1. **Column Detection:**
   - Reads CSV header row
   - Detects all column names
   - Cleans names (spaces → underscores, etc.)

2. **Type Detection:**
   - Analyzes sample rows (first 10)
   - Detects types:
     - Integer (all digits)
     - Numeric (decimal numbers)
     - Text (everything else)

3. **Delimiter Detection:**
   - Tries: comma (`,`), semicolon (`;`), tab (`\t`)
   - Uses most common delimiter

4. **Table Creation:**
   - Creates PostgreSQL table with detected structure
   - Column names cleaned (spaces → underscores)
   - Types assigned based on sample data

5. **Data Import:**
   - Reads CSV file
   - Inserts rows in batches (1000 at a time)
   - Handles encoding (UTF-8 with BOM)

---

## 📝 CSV File Requirements

### Format:
- **Headers:** First row must contain column names
- **Encoding:** UTF-8 (with or without BOM)
- **Delimiter:** Comma (`,`), semicolon (`;`), or tab (`\t`)
- **Quotes:** Optional (handles quoted values)

### Example CSV:
```csv
id,name,description,status,created_date
1,Project A,Description of project A,Active,2024-01-01
2,Project B,Description of project B,Pending,2024-01-02
```

---

## 🚀 Usage Example

### Complete Flow with CSV:

```bash
# Step 1: Export from SQL Server (example)
# (User does this manually)

# Step 2: Run setup wizard
python scripts/setup/setup_embeddings.py

# Wizard asks:
# - Database connection? [uses .env]
# - Import CSV or use existing table? [choose CSV]
# - CSV file path? [enter: data.csv]
# - Table name? [enter: imported_data]
# 
# Script automatically:
# ✓ Analyzes CSV structure
# ✓ Creates PostgreSQL table
# ✓ Imports all data
# ✓ Continues with embedding setup

# Step 3: Generate embeddings
python scripts/core/generate_embeddings_universal.py
```

---

## ⚙️ CSV Import Options

### Standalone CSV Import:

You can also import CSV separately (without running full setup):

```bash
python scripts/helpers/import_csv_to_postgres.py data.csv my_table
```

**What it does:**
- Analyzes CSV file
- Creates PostgreSQL table
- Imports all data
- Reports results

**Useful for:**
- Testing CSV import
- Importing multiple CSV files
- Importing before running setup wizard

---

## 🔍 What Gets Created

### PostgreSQL Table:
- **Name:** User-specified (e.g., `imported_data`)
- **Columns:** From CSV headers (cleaned)
- **Types:** Auto-detected from sample data
- **Data:** All rows from CSV

### Example:
```sql
CREATE TABLE imported_data (
    "id" INTEGER,
    "name" TEXT,
    "description" TEXT,
    "status" TEXT,
    "created_date" TEXT
);
```

---

## ⚠️ Important Notes

1. **Column Name Cleaning:**
   - Spaces → underscores
   - Special characters → removed or replaced
   - Example: "Project Name" → "Project_Name"

2. **Type Detection:**
   - Based on sample rows (first 10)
   - May not be 100% accurate
   - Can be adjusted manually after import

3. **Large Files:**
   - Processes in batches (1000 rows at a time)
   - Memory-efficient
   - Progress shown during import

4. **Encoding:**
   - Handles UTF-8 with BOM
   - Handles regular UTF-8
   - May have issues with other encodings

---

## 🆘 Troubleshooting

### Error: "CSV file not found"
- Check file path (use absolute path if needed)
- Check file exists
- Check file permissions

### Error: "Cannot detect delimiter"
- CSV may have unusual format
- Try opening in Excel and re-saving as CSV

### Error: "Import failed"
- Check database connection
- Check table name doesn't already exist
- Check CSV format (headers in first row)

### Error: "Encoding error"
- Save CSV as UTF-8
- Remove BOM if present
- Check for special characters

---

## ✅ Summary

**CSV Import Features:**
- ✅ Automatic column detection
- ✅ Automatic type detection
- ✅ Automatic delimiter detection
- ✅ Batch processing (efficient)
- ✅ Integrated with setup wizard
- ✅ Standalone import option

**Use Cases:**
- ✅ SQL Server → PostgreSQL
- ✅ MySQL → PostgreSQL
- ✅ Oracle → PostgreSQL
- ✅ Any database → PostgreSQL (via CSV export)

**Result:**
- CSV data imported to PostgreSQL
- Ready for embedding generation
- Works seamlessly with setup wizard

