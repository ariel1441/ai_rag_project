#!/usr/bin/env python3
"""
Detailed scan of the specific workspace for chat data
"""
import os
import json
from pathlib import Path

appdata = os.getenv('APPDATA')
workspace_id = '0cd3ede1a5c7331b4b8db62309a7af8c'
workspace_dir = Path(appdata) / "Cursor" / "User" / "workspaceStorage" / workspace_id

print("=" * 70)
print("DETAILED WORKSPACE SCAN")
print("=" * 70)
print(f"\nWorkspace: {workspace_id}")
print(f"Path: {workspace_dir}\n")

if not workspace_dir.exists():
    print("ERROR: Workspace directory not found!")
    exit(1)

# List all items in workspace
print("=== All items in workspace ===")
for item in sorted(workspace_dir.iterdir()):
    if item.is_dir():
        print(f"📁 {item.name}/")
        # List contents of subdirectories
        try:
            subitems = list(item.iterdir())
            for subitem in subitems[:10]:  # First 10 items
                if subitem.is_file():
                    size = subitem.stat().st_size
                    print(f"   📄 {subitem.name} ({size} bytes)")
                else:
                    print(f"   📁 {subitem.name}/")
            if len(subitems) > 10:
                print(f"   ... and {len(subitems) - 10} more items")
        except Exception as e:
            print(f"   (Error reading: {e})")
    else:
        size = item.stat().st_size
        print(f"📄 {item.name} ({size} bytes)")

# Check workspace.json
print("\n=== Workspace.json ===")
ws_json = workspace_dir / "workspace.json"
if ws_json.exists():
    try:
        with open(ws_json, 'r', encoding='utf-8') as f:
            ws_data = json.load(f)
            print(json.dumps(ws_data, indent=2))
    except Exception as e:
        print(f"Error reading: {e}")
else:
    print("workspace.json not found")

# Look for cursor-retri specifically
print("\n=== Looking for cursor-retri directory ===")
cursor_retri = workspace_dir / "anysphere.cursor-retri"
if cursor_retri.exists():
    print(f"Found: {cursor_retri}")
    print(f"Contents:")
    try:
        all_items = list(cursor_retri.rglob("*"))
        print(f"Total items: {len(all_items)}")
        
        # Group by type
        files = [f for f in all_items if f.is_file()]
        dirs = [d for d in all_items if d.is_dir()]
        
        print(f"Files: {len(files)}")
        print(f"Directories: {len(dirs)}")
        
        # Show all files
        print("\nAll files:")
        for f in sorted(files):
            size = f.stat().st_size
            rel_path = f.relative_to(cursor_retri)
            print(f"  {rel_path} ({size} bytes)")
            
            # Try to read JSON files
            if f.suffix == '.json' and size < 1000000:  # Less than 1MB
                try:
                    with open(f, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                        if isinstance(data, dict):
                            keys = list(data.keys())[:10]
                            print(f"    Keys: {keys}")
                            # Check for chat-related content
                            if any('chat' in str(k).lower() or 'conversation' in str(k).lower() or 'building' in str(k).lower() for k in data.keys()):
                                print(f"    *** CHAT-RELATED DATA FOUND ***")
                                # Show relevant keys
                                relevant = [k for k in data.keys() if 'chat' in str(k).lower() or 'conversation' in str(k).lower() or 'building' in str(k).lower()]
                                print(f"    Relevant keys: {relevant}")
                except:
                    pass
    except Exception as e:
        print(f"Error reading cursor-retri: {e}")
else:
    print("cursor-retri directory NOT FOUND")
    print("This might mean:")
    print("  1. Chat data is stored elsewhere")
    print("  2. Chat data is in cloud storage (Cursor Pro Teams)")
    print("  3. Chat was never saved locally")

# Check for other possible storage locations
print("\n=== Checking for other storage patterns ===")
# Look for any JSON files in workspace root
json_files = list(workspace_dir.glob("*.json"))
if json_files:
    print(f"JSON files in root: {len(json_files)}")
    for jf in json_files:
        print(f"  - {jf.name}")

# Look for any files with "building" in name
all_files = list(workspace_dir.rglob("*"))
building_files = [f for f in all_files if 'building' in f.name.lower()]
if building_files:
    print(f"\n*** FILES WITH 'BUILDING' IN NAME: {len(building_files)} ***")
    for bf in building_files:
        print(f"  - {bf.relative_to(workspace_dir)}")

print("\n" + "=" * 70)








