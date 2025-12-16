"""
Download Mistral-7B-Instruct model for RAG.
Downloads full precision version (~15GB) to D: drive.
"""
import os
import sys
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
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
print("Downloading Mistral-7B-Instruct Model (Full Precision)")
print("=" * 80)
print()
print("Model: mistralai/Mistral-7B-Instruct-v0.2")
print("Size: ~15GB (full precision)")
print("Quality: Best (100%)")
print()

# Determine download location
# Check if we're on D: drive, if not, use D: drive
current_path = Path(__file__).resolve()
if str(current_path).startswith('D:'):
    # Already on D: drive
    base_path = current_path.parent.parent.parent
else:
    # Use D: drive
    base_path = Path("D:/ai_learning/train_ai_tamar_request")

models_dir = base_path / "models" / "llm"
models_dir.mkdir(parents=True, exist_ok=True)

print(f"Download location: {models_dir}")
print()
print("⚠️  This will download ~15GB. Make sure you have:")
print("   - Enough disk space (15GB+)")
print("   - Stable internet connection")
print("   - Time (30-60 minutes depending on speed)")
print()

# Check if running interactively
try:
    response = input("Continue? (yes/no, default=yes): ").strip().lower()
    if response and response not in ['yes', 'y', '']:
        print("Download cancelled.")
        sys.exit(0)
except (EOFError, KeyboardInterrupt):
    # Non-interactive mode - auto-confirm
    print("Non-interactive mode - proceeding with download...")
    print()

print()
print("Starting download...")
print("=" * 80)
print()

try:
    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    
    print(f"Step 1: Downloading model files...")
    print(f"Model: {model_name}")
    print()
    
    # Download using snapshot_download for better control
    print("Downloading model files (this may take 30-60 minutes)...")
    print("Progress will be shown below:")
    print()
    
    model_path = snapshot_download(
        repo_id=model_name,
        cache_dir=str(models_dir),
        local_dir=str(models_dir / "mistral-7b-instruct"),
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
        str(models_dir / "mistral-7b-instruct"),
        local_files_only=True
    )
    print("✅ Tokenizer loaded successfully")
    print()
    
    # Check model files
    model_files = list((models_dir / "mistral-7b-instruct").glob("*.safetensors"))
    model_files.extend((models_dir / "mistral-7b-instruct").glob("*.bin"))
    
    if model_files:
        print(f"✅ Found {len(model_files)} model weight file(s)")
        total_size = sum(f.stat().st_size for f in model_files)
        print(f"✅ Total model size: {total_size / (1024**3):.2f} GB")
    else:
        print("⚠️  Warning: Could not find model weight files")
    
    print()
    print("=" * 80)
    print("✅ DOWNLOAD COMPLETE!")
    print("=" * 80)
    print()
    print(f"Model saved to: {models_dir / 'mistral-7b-instruct'}")
    print()
    print("Next steps:")
    print("  1. Model is ready to use")
    print("  2. We'll create the RAG script next")
    print("  3. The model will be loaded when you run RAG queries")
    print()
    print("Note: First load will take 30-60 seconds (loading into memory)")
    print("      Subsequent queries will be faster (5-15 seconds per answer)")
    print()
    
except KeyboardInterrupt:
    print()
    print("⚠️  Download interrupted by user")
    print("   You can resume by running this script again")
    print("   (It will continue from where it left off)")
    sys.exit(1)
    
except Exception as e:
    print()
    print(f"❌ Error during download: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Check internet connection")
    print("  2. Check disk space (need 15GB+)")
    print("  3. Check if D: drive is accessible")
    print("  4. Try running again (will resume if partially downloaded)")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)

