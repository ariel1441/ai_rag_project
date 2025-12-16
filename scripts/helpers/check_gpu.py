"""
Check if GPU is available and can be used for RAG.
"""
import sys

print("=" * 80)
print("GPU Detection & Setup Check")
print("=" * 80)
print()

# Check if PyTorch is installed
try:
    import torch
    print("✅ PyTorch installed")
    print(f"   Version: {torch.__version__}")
except ImportError:
    print("❌ PyTorch not installed")
    print("   Install with: pip install torch")
    print()
    print("   For GPU support, install CUDA version:")
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    sys.exit(1)

print()

# Check CUDA availability
if torch.cuda.is_available():
    print("✅ CUDA available - GPU detected!")
    print()
    
    # Get GPU info
    gpu_count = torch.cuda.device_count()
    print(f"Number of GPUs: {gpu_count}")
    print()
    
    for i in range(gpu_count):
        gpu_name = torch.cuda.get_device_name(i)
        gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024 ** 3)
        print(f"GPU {i}: {gpu_name}")
        print(f"  VRAM: {gpu_memory:.2f} GB")
        print()
        
        # Check if enough VRAM
        if gpu_memory >= 16:
            print(f"  ✅ Can run FULL PRECISION (15GB) model")
            print(f"  ✅ Can run QUANTIZED (4GB) model")
        elif gpu_memory >= 8:
            print(f"  ✅ Can run QUANTIZED (4GB) model")
            print(f"  ⚠️  Full precision might not fit")
        elif gpu_memory >= 4:
            print(f"  ⚠️  Can run QUANTIZED (4GB) model (tight fit)")
            print(f"  ❌ Full precision won't fit")
        else:
            print(f"  ❌ Not enough VRAM for model")
            print(f"     Need at least 4GB for quantized model")
        
        print()
    
    # Test GPU computation
    print("Testing GPU computation...")
    try:
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        print("  ✅ GPU computation works!")
        print()
    except Exception as e:
        print(f"  ❌ GPU computation failed: {e}")
        print()
    
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("✅ GPU is available and ready to use!")
    print()
    print("Benefits of using GPU:")
    print("  • Model loading: 30-60 seconds (vs 5-10 minutes on CPU)")
    print("  • Answer generation: 5-15 seconds (vs 10-30 minutes on CPU)")
    print("  • No memory fragmentation issues (separate VRAM)")
    print("  • Much faster overall experience")
    print()
    print("The RAG system will automatically use GPU if available.")
    print("You don't need to change anything - it should work!")
    
else:
    print("❌ No GPU detected - will use CPU")
    print()
    print("Current setup:")
    print("  • Model loading: 5-10 minutes (CPU)")
    print("  • Answer generation: 10-30 minutes (CPU)")
    print("  • May have memory fragmentation issues")
    print()
    print("=" * 80)
    print("How to Enable GPU (if you have NVIDIA GPU)")
    print("=" * 80)
    print()
    print("1. Check if you have NVIDIA GPU:")
    print("   • Open Device Manager → Display adapters")
    print("   • Look for NVIDIA GPU (e.g., NVIDIA GeForce RTX 3060)")
    print()
    print("2. Install CUDA Toolkit:")
    print("   • Download from: https://developer.nvidia.com/cuda-downloads")
    print("   • Install CUDA 11.8 or 12.1 (recommended)")
    print()
    print("3. Install PyTorch with CUDA support:")
    print("   pip uninstall torch torchvision torchaudio")
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print()
    print("4. Verify GPU is detected:")
    print("   python scripts/helpers/check_gpu.py")
    print()
    print("5. Restart your terminal/IDE after installation")
    print()
    print("Note: If you don't have NVIDIA GPU, CPU will work but be slower.")

print()

