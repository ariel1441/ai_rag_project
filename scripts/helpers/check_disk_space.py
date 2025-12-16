"""
Quick script to check folder sizes on C: drive.
Shows top folders by size.
"""
import os
from pathlib import Path

def get_folder_size_fast(folder_path):
    """Get folder size quickly using Windows dir command or quick scan."""
    total_size = 0
    try:
        # Quick scan - only immediate files and first level
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            try:
                if os.path.isfile(item_path):
                    total_size += os.path.getsize(item_path)
                elif os.path.isdir(item_path):
                    # Only scan first level of subdirectories (faster)
                    try:
                        for subitem in os.listdir(item_path):
                            subitem_path = os.path.join(item_path, subitem)
                            if os.path.isfile(subitem_path):
                                try:
                                    total_size += os.path.getsize(subitem_path)
                                except:
                                    pass
                    except:
                        pass
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass
    return total_size / (1024 ** 3)  # Convert to GB

def get_folder_size(folder_path):
    """Get total size - use fast method for quick overview."""
    return get_folder_size_fast(folder_path)

def check_c_drive_folders():
    """Check sizes of top-level folders on C: drive."""
    c_drive = Path("C:/")
    
    print("=" * 80)
    print("C: Drive Folder Sizes")
    print("=" * 80)
    print()
    print("Scanning C: drive... This may take a few minutes.")
    print()
    
    folders = []
    
    try:
        for item in c_drive.iterdir():
            if item.is_dir():
                folder_name = item.name
                print(f"Scanning: {folder_name}...", end=" ", flush=True)
                try:
                    size_gb = get_folder_size(item)
                    folders.append((folder_name, size_gb))
                    print(f"{size_gb:.2f} GB")
                except Exception as e:
                    print(f"Error: {e}")
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
    
    for folder_name, size_gb in folders[:20]:  # Top 20
        print(f"{folder_name:<40} {size_gb:>15.2f}")
    
    total_size = sum(size for _, size in folders)
    print("-" * 80)
    print(f"{'Total (shown)':<40} {total_size:>15.2f}")
    print()
    
    # Show available space
    try:
        import shutil
        total, used, free = shutil.disk_usage("C:/")
        print(f"Total C: drive space: {total / (1024**3):.2f} GB")
        print(f"Used: {used / (1024**3):.2f} GB")
        print(f"Free: {free / (1024**3):.2f} GB")
    except Exception as e:
        print(f"Could not get disk usage: {e}")
    
    print()

if __name__ == "__main__":
    check_c_drive_folders()

