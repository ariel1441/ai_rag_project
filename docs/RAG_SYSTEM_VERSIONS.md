# RAG System Versions - Design Documentation

## 📋 Overview

We maintain **two versions** of the RAG system:

1. **High-End Version** (`rag_query_high_end.py`) - Optimal, no compromises
2. **Compatible Version** (`rag_query.py`) - Works on limited systems

## 🚀 High-End Version (`rag_query_high_end.py`)

### Purpose
For servers or high-end PCs with:
- ✅ 16GB+ RAM
- ✅ GPU support (optional but recommended)
- ✅ No memory limitations
- ✅ Production environments

### Features
- **4-bit quantization** (~4GB RAM usage)
- **GPU acceleration** if available
- **No compromises** - uses best settings
- **Optimal performance** - fastest and most efficient

### Usage
```python
from scripts.core.rag_query_high_end import HighEndRAGSystem

rag = HighEndRAGSystem()
rag.connect_db()
rag.load_model()  # Uses 4-bit quantization

result = rag.query("כמה פניות יש מיניב ליבוביץ?")
print(result['answer'])
```

### Requirements
- Python 3.13 or earlier (bitsandbytes support)
- 16GB+ RAM recommended
- bitsandbytes library installed
- GPU optional but recommended

### When to Use
- ✅ Production servers
- ✅ High-end development machines
- ✅ When you have 16GB+ RAM
- ✅ When you want best performance

---

## 💻 Compatible Version (`rag_query.py`)

### Purpose
For systems with limitations:
- ✅ Windows CPU systems
- ✅ Limited RAM (8-12GB)
- ✅ Memory fragmentation issues
- ✅ Systems where 4-bit quantization doesn't work

### Features
- **Automatic detection** - skips 4-bit on Windows CPU
- **float16 loading** (~7-8GB RAM usage)
- **Memory-efficient** - works around fragmentation
- **Compatible** - works on more systems

### Usage
```python
from scripts.core.rag_query import RAGSystem

rag = RAGSystem()
rag.connect_db()
rag.load_model()  # Automatically uses float16 on Windows

result = rag.query("כמה פניות יש מיניב ליבוביץ?")
print(result['answer'])
```

### Requirements
- Python 3.13+ (works on all versions)
- 8GB+ RAM (10GB+ recommended)
- Works on CPU-only systems
- No special libraries needed

### When to Use
- ✅ Windows development machines
- ✅ Limited RAM systems
- ✅ When 4-bit quantization fails
- ✅ When you need maximum compatibility

---

## 🔄 Key Differences

| Feature | High-End Version | Compatible Version |
|---------|-----------------|-------------------|
| **Quantization** | 4-bit (4GB RAM) | float16 (7-8GB RAM) |
| **GPU Support** | Auto-detects & uses | CPU-only (more stable) |
| **Windows CPU** | May hang (known issue) | Skips 4-bit automatically |
| **Memory Usage** | ~4GB | ~7-8GB |
| **Performance** | Fastest | Good |
| **Compatibility** | Requires bitsandbytes | Works everywhere |
| **Best For** | Servers, high-end PCs | Limited systems, Windows |

---

## 🎯 Design Decisions

### Why Two Versions?

**Problem:**
- 4-bit quantization is optimal (4GB RAM, best performance)
- But it has issues on Windows CPU (hangs after loading shards)
- float16 works everywhere but uses more RAM (7-8GB)

**Solution:**
- **High-End Version**: Uses 4-bit (optimal) - for when it works
- **Compatible Version**: Uses float16 (compatible) - for when 4-bit fails

### Why Not Just Use float16 Everywhere?

**Answer:**
- 4-bit quantization is **better** when it works:
  - Uses less RAM (4GB vs 7-8GB)
  - Faster inference
  - Better for production servers
- We want the **best** when possible, but **compatible** when needed

### Why Not Fix 4-bit on Windows?

**Answer:**
- It's a known limitation of bitsandbytes on Windows CPU
- Not something we can fix in our code
- The workaround (float16) works well
- Better to have two versions than compromise everywhere

---

## 📝 Original Design (Optimal Conditions)

### Original Intent
The system was designed for **optimal conditions**:
- 4-bit quantization (4GB RAM)
- GPU acceleration
- Fast inference
- Best performance

### Current Reality
- Windows CPU has limitations
- Memory fragmentation issues
- Need compatible version

### Future Plans
When you have a **strong PC or server**:
- Use `HighEndRAGSystem` (high-end version)
- Get optimal performance
- Use 4-bit quantization
- GPU acceleration

---

## 🧪 Testing

### Test High-End Version
```python
# test_high_end.py
from scripts.core.rag_query_high_end import HighEndRAGSystem

rag = HighEndRAGSystem()
rag.connect_db()
rag.load_model()  # Should use 4-bit quantization
result = rag.query("כמה פניות יש מיניב ליבוביץ?")
print(result['answer'])
```

### Test Compatible Version
```python
# test_compatible.py
from scripts.core.rag_query import RAGSystem

rag = RAGSystem()
rag.connect_db()
rag.load_model()  # Should use float16 on Windows
result = rag.query("כמה פניות יש מיניב ליבוביץ?")
print(result['answer'])
```

---

## 🔧 Migration Guide

### Switching from Compatible to High-End

**If you upgrade your system:**
1. Install bitsandbytes: `pip install bitsandbytes`
2. Change import:
   ```python
   # Old
   from scripts.core.rag_query import RAGSystem
   
   # New
   from scripts.core.rag_query_high_end import HighEndRAGSystem
   ```
3. Change class name:
   ```python
   # Old
   rag = RAGSystem()
   
   # New
   rag = HighEndRAGSystem()
   ```
4. That's it! Everything else is the same.

### Switching from High-End to Compatible

**If you have issues:**
1. Change import:
   ```python
   # Old
   from scripts.core.rag_query_high_end import HighEndRAGSystem
   
   # New
   from scripts.core.rag_query import RAGSystem
   ```
2. Change class name:
   ```python
   # Old
   rag = HighEndRAGSystem()
   
   # New
   rag = RAGSystem()
   ```
3. That's it! Everything else is the same.

---

## 📊 Performance Comparison

### High-End Version (4-bit quantization)
- **RAM Usage**: ~4GB
- **Loading Time**: 30-60 seconds
- **Inference Speed**: Fast (GPU) or Good (CPU)
- **Quality**: 95-98% of full precision

### Compatible Version (float16)
- **RAM Usage**: ~7-8GB
- **Loading Time**: 2-5 minutes
- **Inference Speed**: Good (CPU)
- **Quality**: 100% (same as full precision!)

**Note:** float16 quality is actually **better** than 4-bit (100% vs 95-98%), but uses more RAM.

---

## ✅ Summary

**Two versions for two scenarios:**

1. **High-End** (`rag_query_high_end.py`):
   - Best performance
   - 4-bit quantization
   - GPU support
   - For servers/high-end PCs

2. **Compatible** (`rag_query.py`):
   - Maximum compatibility
   - float16 loading
   - CPU-only
   - For limited systems

**Both use the same:**
- Query parsing
- Database search
- Context formatting
- Answer generation

**Only difference:**
- Model loading method (4-bit vs float16)
- Device handling (GPU vs CPU)

**Choose based on your system capabilities!**

