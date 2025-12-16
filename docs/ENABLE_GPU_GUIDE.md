# How to Enable GPU for RAG System

## 🔍 Current Status

**Your system:**
- ✅ PyTorch installed (version 2.9.1+cpu)
- ❌ CPU-only version (no GPU support)
- ❌ No GPU detected

**This means:**
- Model loading: 5-10 minutes (CPU)
- Answer generation: 10-30 minutes (CPU)
- Memory fragmentation issues possible

---

## ✅ Step 1: Check if You Have GPU

### Windows:
1. Open **Device Manager** (Win + X → Device Manager)
2. Expand **Display adapters**
3. Look for **NVIDIA** GPU (e.g., "NVIDIA GeForce RTX 3060")

**If you see NVIDIA GPU:**
- ✅ You can use GPU! Continue to Step 2.

**If you don't see NVIDIA GPU:**
- ❌ No GPU available - CPU is your only option
- ⚠️ GPU would help a lot, but CPU will work (just slower)

---

## ✅ Step 2: Install CUDA Toolkit

**Why:** PyTorch needs CUDA to communicate with NVIDIA GPU

1. **Download CUDA Toolkit:**
   - Go to: https://developer.nvidia.com/cuda-downloads
   - Select: Windows → x86_64 → 10/11 → exe (local)
   - **Recommended version:** CUDA 11.8 or 12.1

2. **Install CUDA:**
   - Run the installer
   - Follow default options
   - **Note:** Installation takes 10-15 minutes

3. **Verify installation:**
   ```powershell
   nvcc --version
   ```
   Should show CUDA version (e.g., "release 11.8")

---

## ✅ Step 3: Install PyTorch with CUDA Support

**Current:** CPU-only version (`torch 2.9.1+cpu`)
**Need:** CUDA version (`torch 2.9.1+cu118`)

### Option A: CUDA 11.8 (Recommended)
```powershell
# Activate virtual environment
.\venv\Scripts\activate.ps1

# Uninstall CPU version
pip uninstall torch torchvision torchaudio -y

# Install CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Option B: CUDA 12.1
```powershell
# Activate virtual environment
.\venv\Scripts\activate.ps1

# Uninstall CPU version
pip uninstall torch torchvision torchaudio -y

# Install CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Note:** Match CUDA version with what you installed in Step 2!

---

## ✅ Step 4: Verify GPU is Detected

```powershell
# Activate virtual environment
.\venv\Scripts\activate.ps1

# Check GPU
python scripts/helpers/check_gpu.py
```

**Expected output:**
```
✅ CUDA available - GPU detected!
Number of GPUs: 1
GPU 0: NVIDIA GeForce RTX 3060
  VRAM: 12.00 GB
  ✅ Can run QUANTIZED (4GB) model
  ✅ GPU computation works!
```

---

## ✅ Step 5: Test RAG with GPU

Once GPU is detected, the RAG system will **automatically use it**!

**Benefits:**
- ✅ Model loading: **30-60 seconds** (vs 5-10 minutes on CPU)
- ✅ Answer generation: **5-15 seconds** (vs 10-30 minutes on CPU)
- ✅ No memory fragmentation (GPU has separate VRAM)
- ✅ Much faster overall experience

**Test it:**
```powershell
# Activate virtual environment
.\venv\Scripts\activate.ps1

# Test RAG (will automatically use GPU if available)
python scripts/tests/test_rag_compatible.py
```

---

## 🎯 Will GPU Help?

### YES, if you have NVIDIA GPU:
- ✅ **10-100x faster** inference
- ✅ **No memory fragmentation** (separate VRAM)
- ✅ **Much better experience** overall
- ✅ **Worth the setup time** (30 minutes to install)

### NO, if you don't have GPU:
- ❌ Can't use GPU (need NVIDIA GPU)
- ⚠️ CPU will work but be slower
- 💡 Consider: API-based LLM (no local model needed)

---

## 🔧 Troubleshooting

### Issue: "CUDA not available" after installation

**Check:**
1. Did you install CUDA Toolkit? (`nvcc --version`)
2. Did you install PyTorch CUDA version? (check with `python -c "import torch; print(torch.cuda.is_available())"`)
3. Did you restart terminal/IDE after installation?
4. Is your GPU NVIDIA? (AMD GPUs don't work with CUDA)

**Solution:**
- Restart computer
- Reinstall PyTorch CUDA version
- Check GPU in Device Manager

### Issue: "Out of memory" on GPU

**Check VRAM:**
- Need at least 4GB VRAM for quantized model
- Need 8GB+ VRAM for better performance

**Solution:**
- Use quantized model (4GB) - already configured
- Close other GPU applications
- Use CPU if GPU VRAM is too small

### Issue: GPU detected but still using CPU

**Check code:**
- RAG system should auto-detect GPU
- Check `scripts/core/rag_query.py` - should use `device_map="auto"` if GPU available

**Solution:**
- Code already configured to use GPU if available
- If still using CPU, check GPU detection: `python scripts/helpers/check_gpu.py`

---

## 📊 Expected Performance

### CPU (Current):
- Model loading: 5-10 minutes
- Answer generation: 10-30 minutes
- Total first query: 15-40 minutes

### GPU (After setup):
- Model loading: 30-60 seconds
- Answer generation: 5-15 seconds
- Total first query: 1-2 minutes

**Improvement: 10-20x faster!**

---

## 💡 Summary

1. **Check if you have NVIDIA GPU** (Device Manager)
2. **Install CUDA Toolkit** (if you have GPU)
3. **Install PyTorch CUDA version** (replace CPU version)
4. **Verify GPU detection** (`python scripts/helpers/check_gpu.py`)
5. **Test RAG** (will automatically use GPU)

**If you have GPU:** Definitely worth it! 10-20x faster.
**If you don't have GPU:** CPU will work, just slower. Consider API-based LLM.

