"""
Check Memory Before Model Loading
This helps diagnose memory issues before attempting to load the model.
"""
import sys
import psutil
from pathlib import Path

def format_bytes(bytes_val):
    """Format bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def main():
    print("="*80)
    print("MEMORY CHECK BEFORE MODEL LOADING")
    print("="*80)
    print()
    
    # Get memory info
    mem = psutil.virtual_memory()
    
    print("System Memory:")
    print(f"  Total RAM: {format_bytes(mem.total)}")
    print(f"  Available RAM: {format_bytes(mem.available)}")
    print(f"  Used RAM: {format_bytes(mem.used)}")
    print(f"  Percent Used: {mem.percent}%")
    print()
    
    # Check if we have enough for float16 model
    available_gb = mem.available / (1024**3)
    needed_gb = 8.0  # Need ~8GB for float16 model
    
    print("Model Loading Requirements:")
    print(f"  Need: ~{needed_gb} GB free RAM (for float16 model)")
    print(f"  Available: {available_gb:.2f} GB")
    print()
    
    if available_gb >= needed_gb:
        print("✅ SUFFICIENT MEMORY")
        print(f"   You have {available_gb:.2f} GB free, need {needed_gb} GB")
        print("   Model loading should work (if no fragmentation)")
    else:
        print("❌ INSUFFICIENT MEMORY")
        print(f"   You have {available_gb:.2f} GB free, need {needed_gb} GB")
        print("   Model loading will likely fail")
        print()
        print("Solutions:")
        print("  1. Close other applications")
        print("  2. Restart computer to free cached RAM")
        print("  3. Need at least 8GB free RAM")
    
    print()
    print("="*80)
    print("MEMORY FRAGMENTATION WARNING")
    print("="*80)
    print()
    print("Even with sufficient total RAM, Windows memory fragmentation")
    print("can prevent allocating large contiguous blocks needed for model loading.")
    print()
    print("If model loading fails despite having enough RAM:")
    print("  1. Restart computer (clears fragmentation)")
    print("  2. Close all applications")
    print("  3. Run test immediately after restart")
    print()
    
    # Check process memory
    process = psutil.Process()
    process_mem = process.memory_info()
    print("Current Process Memory:")
    print(f"  RSS (Resident Set Size): {format_bytes(process_mem.rss)}")
    print(f"  VMS (Virtual Memory Size): {format_bytes(process_mem.vms)}")
    print()

if __name__ == '__main__':
    main()

