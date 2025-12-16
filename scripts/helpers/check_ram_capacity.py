"""
Check if system can actually use all 32GB RAM.
Verifies Windows sees all RAM and there are no hardware limitations.
"""
import psutil
import platform
import subprocess

def check_ram_capacity():
    """Check RAM capacity and usage."""
    print("=" * 80)
    print("RAM Capacity Check")
    print("=" * 80)
    print()
    
    # Python sees
    ram = psutil.virtual_memory()
    total_gb = ram.total / (1024 ** 3)
    
    print("Python/psutil reports:")
    print(f"  Total RAM: {total_gb:.2f} GB")
    print()
    
    # Windows systeminfo
    print("Windows systeminfo reports:")
    try:
        result = subprocess.run(
            ['systeminfo'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        for line in result.stdout.split('\n'):
            if 'Total Physical Memory' in line or 'זיכרון פיזי כולל' in line:
                print(f"  {line.strip()}")
            if 'Available Physical Memory' in line or 'זיכרון פיזי זמין' in line:
                print(f"  {line.strip()}")
    except:
        print("  Could not get systeminfo")
    
    print()
    
    # Check if it's a 32-bit vs 64-bit limitation
    print("System Architecture:")
    print(f"  Platform: {platform.machine()}")
    print(f"  Architecture: {platform.architecture()[0]}")
    print(f"  Processor: {platform.processor()}")
    print()
    
    # Check for hardware reserved
    print("RAM Breakdown:")
    print(f"  Total: {total_gb:.2f} GB")
    print(f"  Available: {ram.available / (1024**3):.2f} GB")
    print(f"  Used: {ram.used / (1024**3):.2f} GB")
    print(f"  Percent: {ram.percent:.1f}%")
    print()
    
    # Conclusion
    print("=" * 80)
    print("Conclusion")
    print("=" * 80)
    print()
    
    if total_gb >= 31:
        print("✅ System CAN use all 32GB RAM")
        print("   Python sees ~32GB, so Windows sees it too")
        print()
        print("The issue is:")
        print("  - Other processes using RAM")
        print("  - Windows caching (normal)")
        print("  - Not a hardware limitation")
    else:
        print("⚠️  System might not see all RAM")
        print(f"   Only seeing {total_gb:.2f} GB instead of 32GB")
        print()
        print("Possible causes:")
        print("  - 32-bit Windows (unlikely with 32GB)")
        print("  - Hardware limitation")
        print("  - BIOS setting")
    
    print()

if __name__ == "__main__":
    check_ram_capacity()

