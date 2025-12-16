"""
Download LLM model if not present.

Automatically downloads Mistral-7B-Instruct model if it doesn't exist locally.
"""
import os
import sys
from pathlib import Path
import subprocess

def get_model_path():
    """Get the default model path."""
    current_path = Path(__file__).resolve()
    if str(current_path).startswith('D:'):
        base_path = current_path.parent.parent.parent
    else:
        # Try to detect project root
        base_path = Path(__file__).parent.parent.parent
    return base_path / "models" / "llm" / "mistral-7b-instruct"

def check_model_exists(model_path):
    """Check if model files exist."""
    if not model_path.exists():
        return False
    
    # Check for model files
    model_files = list(model_path.glob("*.safetensors")) + list(model_path.glob("*.bin"))
    config_file = model_path / "config.json"
    tokenizer_file = model_path / "tokenizer.json"
    
    # Need at least config, tokenizer, and some model files
    has_config = config_file.exists()
    has_tokenizer = tokenizer_file.exists()
    has_model_files = len(model_files) > 0
    
    return has_config and has_tokenizer and has_model_files

def download_model(model_path):
    """Download the model from Hugging Face."""
    print("=" * 80)
    print("DOWNLOADING LLM MODEL")
    print("=" * 80)
    print()
    print(f"Model: mistralai/Mistral-7B-Instruct-v0.2")
    print(f"Destination: {model_path}")
    print()
    print("⚠️  This will download ~4-7GB (depending on format)")
    print("⏱️  Estimated time: 30-60 minutes (depends on internet speed)")
    print()
    
    # Create directory
    model_path.mkdir(parents=True, exist_ok=True)
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        print("📥 Starting download...")
        print("   This may take a while, please be patient...")
        print()
        
        # Download model and tokenizer
        # Use local_files_only=False to allow download
        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.2",
            cache_dir=str(model_path.parent),
            local_files_only=False  # Allow download
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.2",
            cache_dir=str(model_path.parent),
            local_files_only=False  # Allow download
        )
        
        # Save to our location
        print()
        print("💾 Saving model to project directory...")
        model.save_pretrained(str(model_path))
        tokenizer.save_pretrained(str(model_path))
        
        print()
        print("✅ Model downloaded and saved successfully!")
        print(f"   Location: {model_path}")
        
        return True
        
    except ImportError:
        print("❌ Error: transformers library not installed")
        print("   Install with: pip install transformers")
        return False
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print()
        print("Alternative: Download manually from Hugging Face:")
        print("   1. Go to: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2")
        print("   2. Download all files")
        print(f"   3. Extract to: {model_path}")
        return False

def main():
    """Main function."""
    model_path = get_model_path()
    
    print("=" * 80)
    print("LLM MODEL CHECKER")
    print("=" * 80)
    print()
    print(f"Checking for model at: {model_path}")
    print()
    
    if check_model_exists(model_path):
        print("✅ Model already exists!")
        print(f"   Location: {model_path}")
        print()
        print("Model is ready to use. No download needed.")
        return 0
    else:
        print("⚠️  Model not found")
        print()
        
        response = input("Download model now? (y/n): ").strip().lower()
        
        if response != 'y':
            print()
            print("Skipping download.")
            print("Model will be downloaded automatically on first RAG query.")
            return 0
        
        print()
        success = download_model(model_path)
        
        if success:
            print()
            print("=" * 80)
            print("SETUP COMPLETE")
            print("=" * 80)
            print()
            print("✅ Model is ready to use!")
            print("   You can now run RAG queries.")
            return 0
        else:
            print()
            print("=" * 80)
            print("DOWNLOAD FAILED")
            print("=" * 80)
            print()
            print("The model will be downloaded automatically on first RAG query.")
            print("Or download manually from Hugging Face.")
            return 1

if __name__ == "__main__":
    exit(main())

