"""
Verify Python 3.13 setup and bitsandbytes compatibility
"""
import sys
import importlib

def test_python_version():
    """Check Python version"""
    print("=" * 60)
    print("PYTHON VERSION CHECK")
    print("=" * 60)
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    print(f"Python Executable: {sys.executable}")
    
    if version.major == 3 and version.minor == 13:
        print("✓ Python 3.13 detected - compatible with bitsandbytes")
        return True
    elif version.major == 3 and version.minor >= 14:
        print("✗ Python 3.14+ detected - bitsandbytes will NOT work")
        return False
    else:
        print(f"? Python {version.major}.{version.minor} - may work but 3.13 recommended")
        return True

def test_bitsandbytes():
    """Test bitsandbytes import and functionality"""
    print("\n" + "=" * 60)
    print("BITSANDBYTES TEST")
    print("=" * 60)
    
    try:
        import bitsandbytes as bnb
        print(f"✓ bitsandbytes imported successfully")
        print(f"  Version: {bnb.__version__}")
        
        # Try to create a quantization config (this is what we use in RAG)
        try:
            from transformers import BitsAndBytesConfig
            config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype="float16",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            print("✓ BitsAndBytesConfig created successfully")
            print("✓ 4-bit quantization configuration is ready")
            return True
        except Exception as e:
            print(f"✗ Failed to create BitsAndBytesConfig: {e}")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import bitsandbytes: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error with bitsandbytes: {e}")
        return False

def test_torch():
    """Test PyTorch installation"""
    print("\n" + "=" * 60)
    print("PYTORCH TEST")
    print("=" * 60)
    
    try:
        import torch
        print(f"✓ PyTorch imported successfully")
        print(f"  Version: {torch.__version__}")
        print(f"  CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA Version: {torch.version.cuda}")
        return True
    except Exception as e:
        print(f"✗ Failed to import torch: {e}")
        return False

def test_transformers():
    """Test transformers library"""
    print("\n" + "=" * 60)
    print("TRANSFORMERS TEST")
    print("=" * 60)
    
    try:
        import transformers
        print(f"✓ transformers imported successfully")
        print(f"  Version: {transformers.__version__}")
        return True
    except Exception as e:
        print(f"✗ Failed to import transformers: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PYTHON 3.13 SETUP VERIFICATION")
    print("=" * 60 + "\n")
    
    results = {
        "Python Version": test_python_version(),
        "PyTorch": test_torch(),
        "Transformers": test_transformers(),
        "BitsAndBytes": test_bitsandbytes()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Python 3.13 setup is working!")
        print("  You can now use 4-bit quantization (4GB model)")
    else:
        print("✗ SOME TESTS FAILED - Please check the errors above")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
