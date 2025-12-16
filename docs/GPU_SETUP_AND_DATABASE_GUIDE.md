# GPU Setup & Database Guide for New PC

## 🎯 Overview

This guide helps you:
1. Set up GPU support for RAG
2. Remove CPU optimizations for better quality
3. Set up database on new PC
4. Test the full RAG system

---

## 🖥️ GPU Setup

### Step 1: Check if You Have GPU

```bash
# Check GPU
python scripts/helpers/check_gpu.py
```

**What you need:**
- NVIDIA GPU (GTX/RTX series)
- CUDA support
- 8GB+ VRAM (for float16) or 4GB+ (for 4-bit quantized)

### Step 2: Install CUDA & PyTorch with GPU

**If you have NVIDIA GPU:**

1. **Install CUDA Toolkit:**
   - Download: https://developer.nvidia.com/cuda-downloads
   - Version: CUDA 11.8 or 12.1 (check PyTorch compatibility)

2. **Install PyTorch with CUDA:**
   ```bash
   # For CUDA 11.8
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # For CUDA 12.1
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

3. **Verify GPU:**
   ```python
   import torch
   print(torch.cuda.is_available())  # Should be True
   print(torch.cuda.get_device_name(0))  # Your GPU name
   ```

### Step 3: Use GPU-Optimized RAG

**Option A: Use the new GPU-optimized version:**
```python
from scripts.core.rag_query_gpu import GPUOptimizedRAGSystem

rag = GPUOptimizedRAGSystem()
rag.connect_db()
answer = rag.query("כמה פניות יש מאור גלילי?", use_llm=True)
```

**Option B: Modify existing version (already done):**
- The `rag_query.py` now automatically uses optimal settings when GPU is detected
- No CPU optimizations when GPU is available

---

## 🗄️ Database Setup

### Option 1: Local PostgreSQL (Recommended)

**You need your own PostgreSQL on the new PC:**

1. **Install PostgreSQL:**
   - Download: https://www.postgresql.org/download/windows/
   - Or use Docker: `docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=password pgvector/pgvector:pg16`

2. **Enable pgvector:**
   ```sql
   CREATE EXTENSION vector;
   ```

3. **Import Database:**
   - From work PC: Export database dump
   - On new PC: Import database dump
   ```bash
   # Export (on work PC)
   pg_dump -h localhost -p 5433 -U postgres -d ai_requests_db -F c -f database_backup.dump
   
   # Import (on new PC)
   pg_restore -h localhost -p 5433 -U postgres -d ai_requests_db -c database_backup.dump
   ```

4. **Create .env file:**
   ```
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5433
   POSTGRES_DATABASE=ai_requests_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   ```

### Option 2: Connect to Work PC Database (If Accessible)

**If work PC database is accessible over network:**

1. **Check if work PC allows remote connections:**
   - PostgreSQL `postgresql.conf`: `listen_addresses = '*'`
   - PostgreSQL `pg_hba.conf`: Allow your IP

2. **Update .env:**
   ```
   POSTGRES_HOST=work_pc_ip_address
   POSTGRES_PORT=5433
   POSTGRES_DATABASE=ai_requests_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=work_pc_password
   ```

**⚠️ Security Note:** Only do this if work PC is on secure network!

### Option 3: Fresh Start (No Data Transfer)

**If you want to start fresh:**

1. **Create new database:**
   ```sql
   CREATE DATABASE ai_requests_db;
   \c ai_requests_db
   CREATE EXTENSION vector;
   ```

2. **Import CSV data:**
   ```bash
   python scripts/helpers/import_csv_to_postgres.py
   ```

3. **Generate embeddings:**
   ```bash
   python scripts/core/generate_embeddings.py
   ```

---

## 🚀 Testing RAG on New PC

### Step 1: Verify Setup

```bash
# Check GPU
python scripts/helpers/check_gpu.py

# Check database
python scripts/setup/setup_new_pc.py

# Check models
python scripts/setup/download_llm_model.py
```

### Step 2: Test RAG with GPU

```python
from scripts.core.rag_query_gpu import GPUOptimizedRAGSystem

# Initialize
rag = GPUOptimizedRAGSystem()
rag.connect_db()

# Test query
query = "כמה פניות יש מאור גלילי?"
result = rag.query(query, use_llm=True)

print(result['answer'])
```

**Expected performance:**
- **GPU:** 5-15 seconds per query
- **CPU:** 5-15 minutes per query

### Step 3: Compare Quality

**CPU Optimized (old):**
- Max tokens: 200
- Greedy decoding
- Shorter, less diverse answers

**GPU Optimized (new):**
- Max tokens: 500
- Sampling with temperature
- Longer, more detailed, more creative answers

---

## 📊 Model Recommendations

### Current Model: Mistral-7B-Instruct

**Pros:**
- ✅ Good quality
- ✅ Multilingual (Hebrew support)
- ✅ Reasonable size (~4-7GB)
- ✅ Already downloaded

**Cons:**
- ⚠️ 7B parameters (slower than smaller models)
- ⚠️ Not the latest model

### Better Options (If You Want to Upgrade):

1. **Mistral-7B-Instruct-v0.3** (newer version)
   - Better quality
   - Same size
   - Download: `mistralai/Mistral-7B-Instruct-v0.3`

2. **Llama 3 8B** (alternative)
   - Very good quality
   - Similar size
   - Download: `meta-llama/Llama-3-8B-Instruct`

3. **Mistral Large** (if you have 24GB+ VRAM)
   - Best quality
   - Much larger (~24GB)
   - Download: `mistralai/Mistral-Large-2407`

**Recommendation:** Stick with Mistral-7B-Instruct for now. It's good quality and you already have it downloaded. Upgrade later if needed.

---

## ✅ Summary

### What Changed:

1. **GPU Support:**
   - Modified `rag_query.py` to detect GPU and use optimal settings
   - Created `rag_query_gpu.py` as dedicated GPU version
   - Removed CPU optimizations when GPU is available

2. **Quality Improvements:**
   - Full 500 token answers (not 200)
   - Sampling with temperature (not greedy)
   - Better, more detailed responses

3. **Database Options:**
   - Local PostgreSQL (recommended)
   - Connect to work PC (if accessible)
   - Fresh start with CSV import

### Next Steps:

1. ✅ Install CUDA & PyTorch with GPU support
2. ✅ Set up PostgreSQL on new PC
3. ✅ Import database or start fresh
4. ✅ Test RAG with GPU
5. ✅ Enjoy fast, high-quality answers!

---

## 🆘 Troubleshooting

### GPU Not Detected:
- Check CUDA installation: `nvidia-smi`
- Check PyTorch: `python -c "import torch; print(torch.cuda.is_available())"`
- Reinstall PyTorch with CUDA support

### Database Connection Failed:
- Check PostgreSQL is running
- Check `.env` file has correct credentials
- Check firewall allows connections

### Model Loading Slow:
- First load is always slow (30-60 seconds)
- Subsequent loads are faster (cached)
- GPU makes it much faster

