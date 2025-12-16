"""
Test RAG model loading to diagnose issues.
This will show the actual error if loading fails.
"""
import sys
import os
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

print("=" * 80)
print("RAG Model Loading Test")
print("=" * 80)
print()

# Check model path
model_path = Path("D:/ai_learning/train_ai_tamar_request/models/llm/mistral-7b-instruct")
print(f"Model path: {model_path}")
print(f"Exists: {model_path.exists()}")
print()

if not model_path.exists():
    print("❌ Model directory not found!")
    print("Please download the model first:")
    print("  python scripts/core/download_rag_model.py")
    sys.exit(1)

# Check required files
required_files = ["config.json", "tokenizer.json"]
model_files = list(model_path.glob("*.safetensors")) + list(model_path.glob("*.bin"))

print("Required files:")
for f in required_files:
    filepath = model_path / f
    exists = filepath.exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {f}")

print()
print("Model weight files:")
if model_files:
    for f in sorted(model_files)[:3]:
        size_gb = f.stat().st_size / (1024 ** 3)
        print(f"  ✅ {f.name} ({size_gb:.2f} GB)")
    print(f"  Total: {len(model_files)} files")
else:
    print("  ❌ No model weight files found!")

print()
print("=" * 80)
print("Testing Model Loading...")
print("=" * 80)
print()

try:
    print("Step 1: Importing transformers...")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    print("✅ Imports successful")
    print()
    
    print("Step 2: Checking PyTorch...")
    print(f"  PyTorch version: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  CUDA device: {torch.cuda.get_device_name(0)}")
    print()
    
    print("Step 3: Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        local_files_only=True
    )
    print("✅ Tokenizer loaded")
    print()
    
    print("Step 4: Loading model (this may take 1-2 minutes)...")
    print("⚠️  This will load ~15GB into RAM")
    print()
    
    # Check available memory
    import psutil
    ram = psutil.virtual_memory()
    free_gb = ram.available / (1024 ** 3)
    print(f"Available RAM: {free_gb:.2f} GB")
    if free_gb < 16:
        print("⚠️  Warning: Less than 16GB free RAM - might fail!")
    print()
    
    # Try loading with float16 to save memory
    print("Loading with float16 (saves memory)...")
    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        local_files_only=True,
        dtype=torch.float16,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True
    )
    
    print()
    print("=" * 80)
    print("✅ MODEL LOADED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Model is ready to use.")
    print("You can now run: python scripts/core/rag_query.py")
    print()
    
except ImportError as e:
    print()
    print("❌ Import Error:")
    print(f"   {e}")
    print()
    print("Solution: Install missing packages")
    print("  pip install transformers torch")
    sys.exit(1)
    
except MemoryError as e:
    print()
    print("❌ Memory Error:")
    print(f"   {e}")
    print()
    print("Solutions:")
    print("  1. Close other applications to free RAM")
    print("  2. Use quantized model (4GB instead of 15GB)")
    print("  3. Restart computer to free memory")
    sys.exit(1)
    
except Exception as e:
    print()
    print("❌ Error loading model:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {e}")
    print()
    print("Full error details:")
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)

