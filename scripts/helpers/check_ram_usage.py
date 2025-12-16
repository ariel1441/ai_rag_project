"""
Check what's using RAM on the system.
Shows top processes by memory usage.
"""
import psutil
import os

def check_ram_usage():
    """Check RAM usage and top processes."""
    print("=" * 80)
    print("RAM Usage Analysis")
    print("=" * 80)
    print()
    
    # Overall RAM
    ram = psutil.virtual_memory()
    total_gb = ram.total / (1024 ** 3)
    available_gb = ram.available / (1024 ** 3)
    used_gb = ram.used / (1024 ** 3)
    percent_used = ram.percent
    
    print(f"Total RAM: {total_gb:.2f} GB")
    print(f"Used RAM: {used_gb:.2f} GB ({percent_used:.1f}%)")
    print(f"Available RAM: {available_gb:.2f} GB")
    print()
    
    # Calculate missing RAM
    missing_gb = total_gb - used_gb - available_gb
    if missing_gb > 0.5:  # More than 500MB unaccounted
        print(f"⚠️  Unaccounted RAM: {missing_gb:.2f} GB")
        print("   (This might be cached by Windows or reserved)")
    print()
    
    # Top processes by memory
    print("=" * 80)
    print("Top 20 Processes by Memory Usage")
    print("=" * 80)
    print()
    print(f"{'Process Name':<40} {'Memory (GB)':>15} {'% of Total':>12}")
    print("-" * 80)
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            mem_mb = proc.info['memory_info'].rss / (1024 ** 2)
            if mem_mb > 50:  # Only show processes using >50MB
                processes.append((proc.info['name'], mem_mb))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Sort by memory
    processes.sort(key=lambda x: x[1], reverse=True)
    
    total_process_memory = 0
    for name, mem_mb in processes[:20]:
        mem_gb = mem_mb / 1024
        percent = (mem_mb / (1024 ** 2)) / total_gb * 100
        print(f"{name[:38]:<40} {mem_gb:>15.2f} {percent:>11.2f}%")
        total_process_memory += mem_mb
    
    print("-" * 80)
    total_process_gb = total_process_memory / 1024
    print(f"{'Total (shown)':<40} {total_process_gb:>15.2f}")
    print()
    
    # System reserved/cached
    cached_gb = (ram.total - ram.available - total_process_memory / 1024) / (1024 ** 2)
    if cached_gb > 1:
        print(f"System/Cached RAM: ~{cached_gb:.2f} GB")
        print("   (Windows uses this for caching - normal)")
    print()
    
    # Check for specific high-usage processes
    print("=" * 80)
    print("High Memory Usage Processes (>1GB)")
    print("=" * 80)
    print()
    
    high_usage = [p for p in processes if p[1] > 1024]  # >1GB
    if high_usage:
        for name, mem_mb in high_usage:
            mem_gb = mem_mb / 1024
            print(f"  {name}: {mem_gb:.2f} GB")
            print(f"    → Consider closing this if not needed")
    else:
        print("  No processes using >1GB")
    print()
    
    # Recommendations
    print("=" * 80)
    print("Recommendations")
    print("=" * 80)
    print()
    
    if available_gb < 16:
        needed = 16 - available_gb
        print(f"⚠️  Need {needed:.2f} GB more free RAM for full model")
        print()
        print("Options:")
        print("  1. Close high-usage processes (see above)")
        print("  2. Restart computer (frees up cached RAM)")
        print("  3. Use quantized model (needs only 6-8GB)")
        print()
        
        if high_usage:
            print("High-usage processes to consider closing:")
            for name, mem_mb in high_usage[:5]:
                mem_gb = mem_mb / 1024
                print(f"  - {name}: {mem_gb:.2f} GB")
    else:
        print("✅ You have enough RAM for full model!")
        print("   Available: {available_gb:.2f} GB (need 16GB)")
    print()

if __name__ == "__main__":
    try:
        check_ram_usage()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

