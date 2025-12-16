"""
Quick script to check folder sizes on C: drive - FAST VERSION.
Uses Windows dir command for faster results.
"""
import subprocess
import os
from pathlib import Path

def get_folder_size_windows(folder_path):
    """Get folder size using Windows dir command (much faster)."""
    try:
        # Use dir command to get folder size
        result = subprocess.run(
            ['cmd', '/c', f'dir /s /-c "{folder_path}"'],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout per folder
        )
        
        # Parse output to find total size
        output = result.stdout
        for line in output.split('\n'):
            if 'bytes' in line.lower() and 'File(s)' in line:
                # Extract number before "bytes"
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'bytes' in part.lower() and i > 0:
                        try:
                            size_str = parts[i-1].replace(',', '')
                            size_bytes = int(size_str)
                            return size_bytes / (1024 ** 3)  # Convert to GB
                        except:
                            pass
    except subprocess.TimeoutExpired:
        return 0  # Timeout - skip this folder
    except Exception:
        pass
    
    return 0

def check_c_drive_folders_quick():
    """Quick check of C: drive folders."""
    c_drive = Path("C:/")
    
    print("=" * 80)
    print("C: Drive Folder Sizes (Quick Scan)")
    print("=" * 80)
    print()
    print("Note: This shows approximate sizes. Large folders may take time.")
    print()
    
    folders = []
    
    # Common folders to check
    common_folders = [
        "Program Files",
        "Program Files (x86)",
        "Users",
        "Windows",
        "ProgramData",
        "AppData",
    ]
    
    try:
        for item in c_drive.iterdir():
            if item.is_dir() and not item.name.startswith('$'):
                folder_name = item.name
                print(f"Checking: {folder_name}...", end=" ", flush=True)
                
                # Skip if it's a system folder that takes too long
                if folder_name in ["Windows", "Program Files", "Program Files (x86)", "Users"]:
                    print("(large, estimating...)")
                    try:
                        size_gb = get_folder_size_windows(item)
                        folders.append((folder_name, size_gb))
                        print(f"  → {size_gb:.2f} GB")
                    except Exception as e:
                        print(f"  → Error or timeout")
                        folders.append((folder_name, 0))
                else:
                    # Quick check for smaller folders
                    try:
                        size_gb = get_folder_size_windows(item)
                        folders.append((folder_name, size_gb))
                        print(f"{size_gb:.2f} GB")
                    except Exception as e:
                        print(f"Error")
                        folders.append((folder_name, 0))
    except PermissionError:
        print("⚠ Permission denied for some folders")
    except Exception as e:
        print(f"Error: {e}")
    
    # Sort by size
    folders.sort(key=lambda x: x[1], reverse=True)
    
    print()
    print("=" * 80)
    print("Top Folders by Size")
    print("=" * 80)
    print()
    print(f"{'Folder':<40} {'Size (GB)':>15}")
    print("-" * 80)
    
    for folder_name, size_gb in folders:
        if size_gb > 0:
            print(f"{folder_name:<40} {size_gb:>15.2f}")
    
    print()
    
    # Show available space
    try:
        import shutil
        total, used, free = shutil.disk_usage("C:/")
        print(f"Total C: drive space: {total / (1024**3):.2f} GB")
        print(f"Used: {used / (1024**3):.2f} GB")
        print(f"Free: {free / (1024**3):.2f} GB")
        print()
        print(f"✅ You have {free / (1024**3):.2f} GB free - plenty for RAG model (~4GB)!")
    except Exception as e:
        print(f"Could not get disk usage: {e}")
    
    print()

if __name__ == "__main__":
    check_c_drive_folders_quick()

