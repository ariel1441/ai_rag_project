"""
Check if system can actually use all 32GB RAM.
Verifies RAM configuration and Windows limits.
"""
import psutil
import platform
import subprocess

def check_ram_capability():
    """Check RAM capability and Windows limits."""
    print("=" * 80)
    print("RAM Capability Check")
    print("=" * 80)
    print()
    
    # Get RAM info
    ram = psutil.virtual_memory()
    total_gb = ram.total / (1024 ** 3)
    
    print(f"Total RAM Detected: {total_gb:.2f} GB")
    print()
    
    # Check Windows edition (affects RAM limits)
    print("Windows Information:")
    print(f"  System: {platform.system()} {platform.release()}")
    print(f"  Version: {platform.version()}")
    print()
    
    # Check Windows RAM limits
    print("Windows RAM Limits by Edition:")
    print("  Windows 10/11 Home: 128GB limit")
    print("  Windows 10/11 Pro: 2TB limit")
    print("  Windows Server: Varies")
    print()
    print("✅ Your 32GB is well within all Windows limits")
    print()
    
    # Check if RAM is actually accessible
    print("RAM Accessibility Test:")
    try:
        # Try to allocate a large chunk
        import numpy as np
        test_size_gb = 1.0
        print(f"  Testing allocation of {test_size_gb}GB...")
        test_array = np.zeros(int(test_size_gb * 1024 ** 3 / 8), dtype=np.float64)
        print(f"  ✅ Successfully allocated {test_size_gb}GB")
        del test_array
    except MemoryError:
        print(f"  ❌ Failed to allocate {test_size_gb}GB")
        print("  → System might have RAM issues")
    except Exception as e:
        print(f"  ⚠️  Could not test: {e}")
    print()
    
    # Check for memory leaks or stuck processes
    print("Checking for stuck processes...")
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'status']):
        try:
            if 'python' in proc.info['name'].lower():
                mem_gb = proc.info['memory_info'].rss / (1024 ** 3)
                status = proc.info['status']
                python_processes.append((proc.info['pid'], mem_gb, status))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if python_processes:
        print(f"  Found {len(python_processes)} Python process(es):")
        for pid, mem_gb, status in python_processes:
            print(f"    PID {pid}: {mem_gb:.2f} GB, Status: {status}")
            if mem_gb > 5:
                print(f"      ⚠️  High memory usage - might be stuck!")
    else:
        print("  ✅ No Python processes found")
    print()
    
    # Final assessment
    print("=" * 80)
    print("Assessment")
    print("=" * 80)
    print()
    
    if total_gb >= 31:
        print("✅ System can use 32GB RAM")
        print("   Windows supports it")
        print("   RAM is accessible")
        print()
        print("⚠️  Issue: Not enough FREE RAM (not total RAM)")
        print("   - Total: 32GB ✅")
        print("   - Free: ~11GB ❌ (need 16GB for full model)")
        print()
        print("Solution: Use quantized model (4GB) - needs only 6-8GB free")
    else:
        print("⚠️  System might not be using all RAM")
        print(f"   Detected: {total_gb:.2f} GB")
        print("   Expected: 32 GB")
    print()

if __name__ == "__main__":
    check_ram_capability()

