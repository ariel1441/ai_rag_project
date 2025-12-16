# Quick Start - For New User

**Fast reference for setting up the project**

---

## ⚡ Quick Setup (5 Steps)

### 1. Install Prerequisites
- Python 3.10+
- PostgreSQL 18+
- pgvector extension

### 2. Install Dependencies
```bash
python -m venv venv
# Windows: .\venv\Scripts\activate.ps1
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Create Database
```sql
CREATE DATABASE ai_requests_db;
\c ai_requests_db
CREATE EXTENSION vector;
```

### 4. Configure Environment
Create `.env` file:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
API_KEY=your_api_key
```

### 5. Import Data & Generate Embeddings
```bash
# Place your CSV in: data/raw/requests.csv
python scripts/helpers/import_csv_to_postgres.py
python scripts/core/generate_embeddings.py
```

**Done!** Test with: `python scripts/core/search.py`

---

## 📖 Full Guide

See `SETUP_GUIDE_FOR_NEW_USER.md` for complete instructions.

---

## 🆘 Quick Troubleshooting

**"Module not found"** → `pip install -r requirements.txt`  
**"Cannot connect to database"** → Check `.env` file  
**"pgvector not found"** → Install pgvector extension  
**"Out of memory"** → Close other apps, restart computer  

---

**For detailed help:** See `SETUP_GUIDE_FOR_NEW_USER.md`

