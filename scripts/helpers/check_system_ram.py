"""
Check system RAM and hardware specs.
"""
import psutil
import platform

def check_ram():
    """Check RAM information."""
    print("=" * 80)
    print("System RAM Information")
    print("=" * 80)
    print()
    
    # Get RAM info
    ram = psutil.virtual_memory()
    
    total_gb = ram.total / (1024 ** 3)
    available_gb = ram.available / (1024 ** 3)
    used_gb = ram.used / (1024 ** 3)
    percent_used = ram.percent
    
    print(f"Total RAM: {total_gb:.2f} GB")
    print(f"Available RAM: {available_gb:.2f} GB")
    print(f"Used RAM: {used_gb:.2f} GB")
    print(f"Percent Used: {percent_used:.1f}%")
    print()
    
    # Recommendation
    print("=" * 80)
    print("RAG Model Recommendation")
    print("=" * 80)
    print()
    
    if total_gb >= 32:
        print("✅ You have 32GB+ RAM - EXCELLENT!")
        print()
        print("Recommendation: Use FULL PRECISION (15GB) model")
        print("  ✅ Best quality (100%)")
        print("  ✅ Plenty of RAM for smooth operation")
        print("  ✅ Can handle complex queries better")
        print("  ✅ No performance issues")
    elif total_gb >= 16:
        print("✅ You have 16GB+ RAM - GOOD!")
        print()
        print("Recommendation: Use FULL PRECISION (15GB) model")
        print("  ✅ Best quality")
        print("  ✅ Should work well")
        print("  ⚠️  May use most of your RAM (but should be fine)")
    elif total_gb >= 8:
        print("⚠️  You have 8-16GB RAM")
        print()
        print("Recommendation: Use QUANTIZED (4GB) model")
        print("  ✅ Still excellent quality (95-98%)")
        print("  ✅ Won't overwhelm your system")
        print("  ✅ Faster loading")
    else:
        print("⚠️  You have less than 8GB RAM")
        print()
        print("Recommendation: Use QUANTIZED (4GB) model")
        print("  ✅ Only option that will work")
        print("  ✅ Still good quality")
    
    print()
    
    # Check GPU if available
    print("=" * 80)
    print("GPU Information (if available)")
    print("=" * 80)
    print()
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            print(f"✅ CUDA available - {gpu_count} GPU(s) detected")
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024 ** 3)
                print(f"  GPU {i}: {gpu_name}")
                print(f"    VRAM: {gpu_memory:.2f} GB")
                
                if gpu_memory >= 16:
                    print(f"    ✅ Can run FULL PRECISION (15GB) model")
                elif gpu_memory >= 8:
                    print(f"    ✅ Can run QUANTIZED (4GB) model")
                    print(f"    ⚠️  Full precision might not fit")
                else:
                    print(f"    ⚠️  Only quantized will work")
        else:
            print("No GPU detected - will use CPU")
            print("  ⚠️  CPU inference is slower (5-15 seconds per answer)")
            print("  ✅ But will work fine with your 32GB RAM!")
    except ImportError:
        print("PyTorch not installed - cannot check GPU")
        print("  (This is fine - we'll install it when setting up RAG)")
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(f"✅ Total RAM: {total_gb:.2f} GB")
    print(f"✅ Available RAM: {available_gb:.2f} GB")
    print()
    
    if total_gb >= 16:
        print("🎯 RECOMMENDATION: Use FULL PRECISION (15GB) model")
        print("   - Best quality")
        print("   - You have plenty of RAM")
        print("   - Will work smoothly")
    else:
        print("🎯 RECOMMENDATION: Use QUANTIZED (4GB) model")
        print("   - Still excellent quality")
        print("   - Better for your system")
    
    print()

if __name__ == "__main__":
    try:
        check_ram()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

