# PostgreSQL Setup for New PC - Local Database

## 🎯 Goal

Set up a **local-only** PostgreSQL database for your RAG project, separate from your external projects.

---

## ✅ What You Already Have

- ✅ PostgreSQL installed
- ✅ 2 existing servers (for external projects)
- ✅ Need: New local database for RAG project

---

## 🔒 Local-Only Configuration

**Your new database will be:**
- ✅ **Local-only** - Only accessible from this PC
- ✅ **Separate** - Won't affect your external projects
- ✅ **Isolated** - Each database is independent

**How it works:**
- Each PostgreSQL server can have multiple databases
- Databases are completely separate
- You can have: `external_project_1`, `external_project_2`, `ai_requests_db` (new)
- All on the same PostgreSQL server, but isolated

---

## 🚀 Quick Setup

### Option 1: Use the Setup Script (Easiest)

```bash
python scripts/setup/setup_local_postgres.py
```

**What it does:**
1. Tests your PostgreSQL connection
2. Creates new database `ai_requests_db`
3. Enables pgvector extension
4. Creates `.env` file with credentials
5. Verifies local-only configuration

**You'll need:**
- PostgreSQL username (usually `postgres`)
- PostgreSQL password (if you forgot, see below)

---

### Option 2: Manual Setup

#### Step 1: Find Your PostgreSQL Credentials

**Option A: Check pgAdmin**
1. Open pgAdmin
2. Look at your existing servers
3. Check the connection details (username, port)

**Option B: Try Defaults**
- Username: `postgres`
- Password: `postgres` (or blank, or what you set during installation)
- Port: `5432` (or check in pgAdmin)

**Option C: Reset Password**
1. Open pgAdmin
2. Right-click server → Properties → Connection tab
3. Or edit `pg_hba.conf` to allow local connections without password temporarily

#### Step 2: Create Database

**Using pgAdmin:**
1. Open pgAdmin
2. Right-click "Databases" → Create → Database
3. Name: `ai_requests_db`
4. Click Save

**Using Command Line:**
```bash
psql -U postgres
CREATE DATABASE ai_requests_db;
\c ai_requests_db
CREATE EXTENSION vector;
\q
```

#### Step 3: Create .env File

Create `.env` file in project root:
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
```

---

## 🔍 Finding Your PostgreSQL Info

### Check pgAdmin

1. **Open pgAdmin**
2. **Look at Servers:**
   - Server name
   - Port number (usually 5432)
   - Username (usually postgres)

3. **To see password:**
   - Right-click server → Properties
   - Go to Connection tab
   - Password is stored (but hidden)

### Check Services

1. **Open Services** (Windows + R → `services.msc`)
2. **Look for PostgreSQL:**
   - `postgresql-x64-16` (or similar)
   - Shows if running
   - Right-click → Properties to see details

### Check Default Location

PostgreSQL config is usually at:
- `C:\Program Files\PostgreSQL\16\data\postgresql.conf`
- `C:\Program Files\PostgreSQL\15\data\postgresql.conf`

---

## 🆘 Forgot Password?

### Option 1: Reset via pgAdmin

1. Open pgAdmin
2. Right-click server → Properties
3. Connection tab → Change password

### Option 2: Reset via Command Line

1. **Edit pg_hba.conf:**
   - Location: `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`
   - Change line: `host all all 127.0.0.1/32 md5`
   - To: `host all all 127.0.0.1/32 trust`
   - Save file

2. **Restart PostgreSQL:**
   - Services → PostgreSQL → Restart

3. **Connect without password:**
   ```bash
   psql -U postgres
   ```

4. **Change password:**
   ```sql
   ALTER USER postgres WITH PASSWORD 'new_password';
   ```

5. **Revert pg_hba.conf:**
   - Change back to `md5`
   - Restart PostgreSQL

### Option 3: Use Windows Authentication

If you're logged in as the PostgreSQL service user, you might be able to connect without password.

---

## ✅ Verify Local-Only Setup

### Check postgresql.conf

1. **Find config file:**
   - Usually: `C:\Program Files\PostgreSQL\16\data\postgresql.conf`

2. **Check `listen_addresses`:**
   ```conf
   listen_addresses = 'localhost'  # ✅ Local-only
   # OR
   listen_addresses = '*'  # ⚠️ Listens on all addresses
   ```

3. **If it's `'*'`, change to `'localhost'`:**
   - Edit file (may need admin)
   - Change: `listen_addresses = 'localhost'`
   - Restart PostgreSQL

### Check pg_hba.conf

1. **Find file:**
   - Usually: `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`

2. **Check local connections:**
   ```
   # IPv4 local connections:
   host    all    all    127.0.0.1/32    md5  # ✅ Local-only
   ```

3. **If you see:**
   ```
   host    all    all    0.0.0.0/0    md5  # ⚠️ Allows all IPs
   ```
   Change to `127.0.0.1/32` for local-only

---

## 🧪 Test Your Setup

```bash
# Test connection
python scripts/setup/setup_local_postgres.py

# Or test manually
python -c "
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DATABASE'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)
print('✅ Connection successful!')
conn.close()
"
```

---

## 📊 Database Structure

**Your PostgreSQL will have:**
```
PostgreSQL Server (port 5432)
├── postgres (default database)
├── external_project_1 (your existing project)
├── external_project_2 (your existing project)
└── ai_requests_db (NEW - for RAG project) ✅
    ├── requests (table)
    ├── request_embeddings (table)
    └── vector extension (pgvector)
```

**All databases are separate:**
- ✅ No interference between projects
- ✅ Different credentials per database (if needed)
- ✅ Can backup/restore independently

---

## 🎯 Summary

1. **Run setup script:**
   ```bash
   python scripts/setup/setup_local_postgres.py
   ```

2. **Enter your PostgreSQL credentials:**
   - Username (usually `postgres`)
   - Password (check pgAdmin or reset if needed)
   - Port (usually `5432`)

3. **Script will:**
   - ✅ Create new database `ai_requests_db`
   - ✅ Enable pgvector
   - ✅ Create `.env` file
   - ✅ Verify local-only setup

4. **Your external projects:**
   - ✅ Won't be affected
   - ✅ Completely separate
   - ✅ Safe to proceed

---

## 🆘 Still Having Issues?

**Common problems:**

1. **"Connection refused":**
   - PostgreSQL not running
   - Start from Services or pgAdmin

2. **"Password authentication failed":**
   - Wrong password
   - Reset password (see above)

3. **"Database already exists":**
   - Use existing database or choose different name

4. **"Extension vector does not exist":**
   - Install pgvector or use Docker version

**Need help?** Run the setup script - it will guide you through each step!

