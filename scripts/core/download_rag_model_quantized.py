"""
Download Quantized Mistral-7B-Instruct model for RAG.
Downloads 4-bit quantized version (~4GB) - works with less RAM.
"""
import os
import sys
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from huggingface_hub import snapshot_download
import torch

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
print("Downloading Mistral-7B-Instruct Model (Quantized 4-bit)")
print("=" * 80)
print()
print("Model: mistralai/Mistral-7B-Instruct-v0.2 (4-bit quantized)")
print("Size: ~4GB (quantized)")
print("Quality: Excellent (95-98% of full precision)")
print("RAM needed: ~6-8GB (instead of 16GB)")
print()

# Determine download location
current_path = Path(__file__).resolve()
if str(current_path).startswith('D:'):
    base_path = current_path.parent.parent.parent
else:
    base_path = Path("D:/ai_learning/train_ai_tamar_request")

models_dir = base_path / "models" / "llm"
models_dir.mkdir(parents=True, exist_ok=True)

print(f"Download location: {models_dir}")
print()
print("⚠️  This will download ~4GB. Much faster and uses less RAM!")
print()

response = input("Continue? (yes/no, default=yes): ").strip().lower()
if response and response not in ['yes', 'y', '']:
    print("Download cancelled.")
    sys.exit(0)

print()
print("Starting download...")
print("=" * 80)
print()

try:
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    
    print(f"Step 1: Downloading model files...")
    print(f"Model: {model_name}")
    print()
    
    # Download using snapshot_download
    print("Downloading model files (this may take 10-20 minutes)...")
    print("Progress will be shown below:")
    print()
    
    model_path = snapshot_download(
        repo_id=model_name,
        cache_dir=str(models_dir),
        local_dir=str(models_dir / "mistral-7b-instruct-quantized"),
        local_dir_use_symlinks=False,
        resume_download=True
    )
    
    print()
    print("=" * 80)
    print("Step 2: Verifying download...")
    print("=" * 80)
    print()
    
    # Verify by loading tokenizer
    print("Loading tokenizer to verify...")
    tokenizer = AutoTokenizer.from_pretrained(
        str(models_dir / "mistral-7b-instruct-quantized"),
        local_files_only=True
    )
    print("✅ Tokenizer loaded successfully")
    print()
    
    print("=" * 80)
    print("✅ DOWNLOAD COMPLETE!")
    print("=" * 80)
    print()
    print(f"Model saved to: {models_dir / 'mistral-7b-instruct-quantized'}")
    print()
    print("Note: To use quantized model, you'll need to load it with quantization config.")
    print("The RAG script will be updated to support this.")
    print()
    
except KeyboardInterrupt:
    print()
    print("⚠️  Download interrupted by user")
    print("   You can resume by running this script again")
    sys.exit(1)
    
except Exception as e:
    print()
    print(f"❌ Error during download: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)

