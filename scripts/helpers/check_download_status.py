"""
Check the status of the model download.
Shows what files have been downloaded and total progress.
"""
import os
from pathlib import Path

def check_download_status():
    """Check model download status."""
    print("=" * 80)
    print("Model Download Status Check")
    print("=" * 80)
    print()
    
    # Check download location
    models_dir = Path("D:/ai_learning/train_ai_tamar_request/models/llm/mistral-7b-instruct")
    
    if not models_dir.exists():
        print("❌ Model directory not found yet")
        print(f"   Expected location: {models_dir}")
        print()
        print("This means:")
        print("   - Download hasn't started yet, OR")
        print("   - Download is in progress (checking cache location)")
        print()
        
        # Check Hugging Face cache
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        if hf_cache.exists():
            print(f"Checking Hugging Face cache: {hf_cache}")
            mistral_dirs = list(hf_cache.glob("*mistral*"))
            if mistral_dirs:
                print(f"✅ Found {len(mistral_dirs)} Mistral-related directories in cache")
                for d in mistral_dirs[:3]:
                    print(f"   - {d.name}")
            else:
                print("   No Mistral files in cache yet")
        return
    
    print(f"✅ Model directory found: {models_dir}")
    print()
    
    # Check for key files
    expected_files = {
        "config.json": "Model configuration",
        "tokenizer.json": "Tokenizer",
        "generation_config.json": "Generation settings",
    }
    
    found_files = []
    missing_files = []
    
    for filename, description in expected_files.items():
        filepath = models_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size / (1024 ** 2)  # MB
            found_files.append((filename, size, description))
        else:
            missing_files.append((filename, description))
    
    # Check for model weight files
    safetensors_files = list(models_dir.glob("*.safetensors"))
    bin_files = list(models_dir.glob("*.bin"))
    model_files = safetensors_files + bin_files
    
    print("File Status:")
    print("-" * 80)
    
    if found_files:
        print("✅ Downloaded files:")
        for filename, size, desc in found_files:
            print(f"   {filename:<30} {size:>8.2f} MB  ({desc})")
        print()
    
    if missing_files:
        print("⏳ Missing files (still downloading):")
        for filename, desc in missing_files:
            print(f"   {filename:<30}  ({desc})")
        print()
    
    if model_files:
        print("✅ Model weight files:")
        total_size = 0
        for model_file in sorted(model_files):
            size = model_file.stat().st_size / (1024 ** 3)  # GB
            total_size += size
            print(f"   {model_file.name:<50} {size:>8.2f} GB")
        print()
        print(f"   Total model size: {total_size:.2f} GB")
        print()
        
        # Estimate progress
        expected_size = 15.0  # GB
        progress = (total_size / expected_size) * 100
        if progress >= 95:  # 95% threshold (some files might be small)
            print("✅ Download appears COMPLETE!")
            print()
            print("Next steps:")
            print("   1. Test RAG: python scripts/core/rag_query.py")
            print("   2. Try queries like: 'כמה פניות יש מאור גלילי?'")
        elif progress >= 50:
            print(f"⏳ Download in progress: ~{progress:.1f}% complete")
            print(f"   Still downloading... ({expected_size - total_size:.2f} GB remaining)")
        else:
            print(f"⏳ Download in progress: ~{progress:.1f}% complete")
            print(f"   Still downloading... ({expected_size - total_size:.2f} GB remaining)")
    else:
        print("⏳ Model weight files not found yet (still downloading)")
        print()
        print("Download is likely still in progress.")
        print("Check the terminal where download is running for progress.")
    
    print()
    print("=" * 80)
    print("How to check download progress:")
    print("=" * 80)
    print()
    print("1. Check terminal where download is running")
    print("   - Look for progress bars")
    print("   - Files download sequentially")
    print()
    print("2. Run this script again:")
    print("   python scripts/helpers/check_download_status.py")
    print()
    print("3. Check file sizes manually:")
    print(f"   dir \"{models_dir}\"")
    print()
    
    # Check if process is running (Windows)
    try:
        import subprocess
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
            capture_output=True,
            text=True
        )
        if 'python.exe' in result.stdout:
            print("✅ Python process is running (download likely in progress)")
        else:
            print("⚠️  No Python process found (download may have finished or stopped)")
    except:
        pass
    
    print()

if __name__ == "__main__":
    check_download_status()
