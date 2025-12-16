"""
Test Model Loading Memory Usage
This tests if we can load the model with 4-bit quantization and check memory usage.
"""
import sys
import os
import psutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

def get_memory_info():
    """Get current memory usage."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    system_mem = psutil.virtual_memory()
    
    return {
        'process_mb': mem_info.rss / (1024 * 1024),
        'system_total_gb': system_mem.total / (1024 ** 3),
        'system_available_gb': system_mem.available / (1024 ** 3),
        'system_used_gb': system_mem.used / (1024 ** 3),
        'system_percent': system_mem.percent
    }

def main():
    print("="*80)
    print("MODEL LOADING MEMORY TEST")
    print("="*80)
    print()
    
    # Check initial memory
    print("Step 1: Checking initial memory...")
    initial_mem = get_memory_info()
    print(f"  Process memory: {initial_mem['process_mb']:.1f} MB")
    print(f"  System total RAM: {initial_mem['system_total_gb']:.1f} GB")
    print(f"  System available RAM: {initial_mem['system_available_gb']:.1f} GB")
    print(f"  System used RAM: {initial_mem['system_used_gb']:.1f} GB ({initial_mem['system_percent']:.1f}%)")
    print()
    
    if initial_mem['system_available_gb'] < 4:
        print("⚠️  WARNING: Less than 4GB free RAM available!")
        print(f"   Available: {initial_mem['system_available_gb']:.1f} GB")
        print("   4-bit quantization needs ~4GB free RAM")
        print("   This may fail!")
        print()
    
    # Import libraries
    print("Step 2: Importing libraries...")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        print(f"  ✅ PyTorch: {torch.__version__}")
        print(f"  ✅ CUDA available: {torch.cuda.is_available()}")
        print()
    except Exception as e:
        print(f"  ❌ Failed to import: {e}")
        return
    
    # Check memory after imports
    after_import_mem = get_memory_info()
    print(f"  Memory after imports: {after_import_mem['process_mb']:.1f} MB")
    print(f"  Memory increase: {after_import_mem['process_mb'] - initial_mem['process_mb']:.1f} MB")
    print()
    
    # Get model path
    current_path = Path(__file__).resolve()
    if str(current_path).startswith('D:'):
        base_path = current_path.parent.parent.parent
    else:
        base_path = Path("D:/ai_learning/train_ai_tamar_request")
    
    model_path = base_path / "models" / "llm" / "mistral-7b-instruct"
    
    if not model_path.exists():
        print(f"❌ Model not found at: {model_path}")
        print("   Please download the model first")
        return
    
    print(f"Step 3: Loading model from: {model_path}")
    print()
    
    # Try 4-bit quantization
    print("Attempting 4-bit quantization...")
    print("⏳ This will take 30-60 seconds...")
    print()
    
    try:
        # Create quantization config
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Check memory before loading
        before_load_mem = get_memory_info()
        print(f"Memory before loading: {before_load_mem['process_mb']:.1f} MB")
        print(f"Available system RAM: {before_load_mem['system_available_gb']:.1f} GB")
        print()
        
        # Load model with explicit CPU device_map
        print("Loading model with 4-bit quantization...")
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            local_files_only=True,
            quantization_config=quantization_config,
            device_map="cpu",  # Force CPU
            low_cpu_mem_usage=True,
            torch_dtype=torch.float16
        )
        
        # Check memory after loading
        after_load_mem = get_memory_info()
        print()
        print("="*80)
        print("✅ MODEL LOADED SUCCESSFULLY!")
        print("="*80)
        print()
        print(f"Memory after loading: {after_load_mem['process_mb']:.1f} MB")
        print(f"Memory increase: {after_load_mem['process_mb'] - before_load_mem['process_mb']:.1f} MB")
        print(f"Memory increase (GB): {(after_load_mem['process_mb'] - before_load_mem['process_mb']) / 1024:.2f} GB")
        print()
        print(f"Available system RAM: {after_load_mem['system_available_gb']:.1f} GB")
        print()
        
        # Test a simple inference
        print("Testing inference...")
        tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        inputs = tokenizer("Hello, how are you?", return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=10)
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"✅ Inference test successful!")
        print(f"   Answer: {answer}")
        print()
        
        # Final memory check
        final_mem = get_memory_info()
        print(f"Final memory: {final_mem['process_mb']:.1f} MB")
        print(f"Total memory used: {final_mem['process_mb'] - initial_mem['process_mb']:.1f} MB")
        print()
        print("="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print()
        print("4-bit quantization is working correctly!")
        print(f"Model uses approximately {(after_load_mem['process_mb'] - before_load_mem['process_mb']) / 1024:.2f} GB RAM")
        
    except RuntimeError as e:
        error_msg = str(e)
        print()
        print("="*80)
        print("❌ MODEL LOADING FAILED")
        print("="*80)
        print()
        print(f"Error: {error_msg}")
        print()
        
        if "not enough memory" in error_msg.lower() or "out of memory" in error_msg.lower():
            current_mem = get_memory_info()
            print("Memory Analysis:")
            print(f"  Available system RAM: {current_mem['system_available_gb']:.1f} GB")
            print(f"  Process memory: {current_mem['process_mb']:.1f} MB")
            print()
            print("Solutions:")
            print("  1. Close other applications to free RAM")
            print("  2. Restart computer to free cached RAM")
            print("  3. Need at least 4GB free RAM for 4-bit quantization")
            print("  4. Try loading with float16 instead (needs ~7-8GB)")
        else:
            print("This might be a different issue. Check the error message above.")
        
    except Exception as e:
        print()
        print("="*80)
        print("❌ UNEXPECTED ERROR")
        print("="*80)
        print()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()


