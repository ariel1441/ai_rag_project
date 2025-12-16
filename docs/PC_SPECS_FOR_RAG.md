# PC Specs Needed for RAG System

## 🎯 Minimum vs Recommended Specs

### Minimum Specs (CPU-Only, Slow but Works)

**CPU:**
- Intel Core i5 (8th gen+) or AMD Ryzen 5 (3000 series+)
- 4+ cores
- **Speed:** 10-30 minutes per query ⚠️

**RAM:**
- 16GB minimum
- 8GB free for model (float16)
- **Note:** 32GB recommended to avoid memory fragmentation

**Storage:**
- 50GB free space
- SSD recommended (faster model loading)

**GPU:**
- Not required (CPU will work)
- But **highly recommended** (100x faster!)

---

### Recommended Specs (GPU-Accelerated, Fast)

**CPU:**
- Intel Core i7/i9 or AMD Ryzen 7/9
- 8+ cores
- **Speed:** 5-15 seconds per query ✅

**RAM:**
- 16GB minimum
- 32GB recommended (for other applications)

**Storage:**
- 50GB free space
- NVMe SSD recommended

**GPU (CRITICAL for speed):**
- NVIDIA GPU with CUDA support
- **Minimum:** 8GB VRAM (for quantized model)
- **Recommended:** 12GB+ VRAM (for better performance)
- **Examples:**
  - RTX 3060 (12GB) ✅ Good
  - RTX 3070 (8GB) ✅ Good
  - RTX 3080 (10GB) ✅ Good
  - RTX 4060 (8GB) ✅ Good
  - RTX 4070 (12GB) ✅ Excellent
  - RTX 4080/4090 (16GB+) ✅ Excellent

**Why GPU matters:**
- CPU: 10-30 minutes per query
- GPU: 5-15 seconds per query
- **100-200x faster!**

---

## 📊 Performance Comparison

### CPU-Only System (Your Current Setup)

**Specs:**
- CPU: Any modern CPU (4+ cores)
- RAM: 16GB+
- GPU: None

**Performance:**
- Model loading: 5-10 minutes (first time)
- Answer generation: 10-30 minutes per query
- **Total per query:** 10-30 minutes

**Use case:** Development, testing, low-volume usage

---

### GPU-Accelerated System (Recommended)

**Specs:**
- CPU: Any modern CPU (4+ cores)
- RAM: 16GB+
- GPU: NVIDIA with 8GB+ VRAM

**Performance:**
- Model loading: 30-60 seconds (first time)
- Answer generation: 5-15 seconds per query
- **Total per query:** 5-15 seconds

**Use case:** Production, high-volume usage, real-time queries

---

## 💰 Cost Comparison

### Option 1: CPU-Only (Current)

**Cost:** $0 (use existing PC)
**Speed:** 10-30 minutes per query
**Best for:** Development, testing, occasional use

### Option 2: Add GPU to Existing PC

**Cost:** $300-800 (GPU)
**Speed:** 5-15 seconds per query
**Best for:** If you have desktop PC with PCIe slot

### Option 3: New PC with GPU

**Cost:** $1,500-3,000 (full PC)
**Speed:** 5-15 seconds per query
**Best for:** New setup, production server

### Option 4: Cloud GPU (AWS, Google Cloud)

**Cost:** $0.50-2.00 per hour
**Speed:** 5-15 seconds per query
**Best for:** Temporary use, testing, no upfront cost

---

## 🎯 Recommendations by Use Case

### Development/Testing

**Minimum:**
- CPU: Any modern CPU
- RAM: 16GB
- GPU: Optional (but recommended)
- **Cost:** Use existing PC

### Production (Internal Server)

**Recommended:**
- CPU: Intel i7/i9 or AMD Ryzen 7/9
- RAM: 32GB
- GPU: NVIDIA RTX 3060 (12GB) or better
- **Cost:** $1,500-2,500

### High-Volume Production

**Best:**
- CPU: Intel i9 or AMD Ryzen 9
- RAM: 64GB
- GPU: NVIDIA RTX 4070 (12GB) or RTX 4080 (16GB)
- **Cost:** $2,500-4,000

---

## 🔍 How to Check Your Current Specs

### Windows:

1. **CPU:**
   - Task Manager → Performance → CPU
   - Or: Settings → System → About

2. **RAM:**
   - Task Manager → Performance → Memory
   - Or: Settings → System → About

3. **GPU:**
   - Device Manager → Display adapters
   - Or: Task Manager → Performance → GPU

4. **Check if GPU is NVIDIA:**
   - Device Manager → Display adapters
   - Look for "NVIDIA" in name

---

## ✅ Your Current Setup Analysis

**From logs:**
- ✅ Model loaded successfully (8:19 minutes)
- ✅ Generation works (32 minutes)
- ⚠️ PyTorch: CPU-only version (2.9.1+cpu)
- ❌ No GPU detected

**What you need:**
1. Check if you have NVIDIA GPU (Device Manager)
2. If yes: Install CUDA PyTorch (see GPU guide)
3. If no: CPU will work, but very slow

**Expected improvement with GPU:**
- Current: 32 minutes per query
- With GPU: 5-15 seconds per query
- **100-200x faster!**

---

## 🚀 Quick Start: Enable GPU (If You Have One)

1. **Check GPU:**
   ```powershell
   # Open Device Manager → Display adapters
   # Look for NVIDIA GPU
   ```

2. **Install CUDA Toolkit:**
   - Download: https://developer.nvidia.com/cuda-downloads
   - Install CUDA 11.8 or 12.1

3. **Install CUDA PyTorch:**
   ```powershell
   .\venv\Scripts\activate.ps1
   pip uninstall torch torchvision torchaudio -y
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

4. **Verify:**
   ```powershell
   python scripts/helpers/check_gpu.py
   ```

5. **Restart server:**
   - GPU will be used automatically!

---

## 📝 Summary

**Minimum (CPU-only):**
- CPU: Any modern (4+ cores)
- RAM: 16GB
- **Speed:** 10-30 min/query

**Recommended (GPU):**
- CPU: Any modern (4+ cores)
- RAM: 16GB
- GPU: NVIDIA 8GB+ VRAM
- **Speed:** 5-15 sec/query

**Your current setup:**
- ✅ Works but slow (32 min/query)
- ⚠️ Need GPU for speed
- 💡 Check if you have NVIDIA GPU!

