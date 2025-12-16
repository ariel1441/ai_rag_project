#!/usr/bin/env python3
"""
READ-ONLY DIAGNOSTIC: Find Cursor chat data
This script only READS files - it makes NO changes
"""
import os
import json
import glob
from pathlib import Path
from datetime import datetime

def find_cursor_chat_data():
    """Find Cursor chat storage locations"""
    appdata = os.getenv('APPDATA')
    localappdata = os.getenv('LOCALAPPDATA')
    
    print("Searching for Cursor chat data...")
    print(f"APPDATA: {appdata}")
    print(f"LOCALAPPDATA: {localappdata}\n")
    
    # Check workspaceStorage directories
    workspace_storage = Path(appdata) / "Cursor" / "User" / "workspaceStorage"
    
    if not workspace_storage.exists():
        print(f"Workspace storage not found at: {workspace_storage}")
        return
    
    print(f"Found workspace storage: {workspace_storage}\n")
    
    # Find all workspace directories
    workspace_dirs = [d for d in workspace_storage.iterdir() if d.is_dir()]
    print(f"Found {len(workspace_dirs)} workspace directories\n")
    
    # Look for cursor-retri directories and chat data
    for ws_dir in workspace_dirs:
        cursor_retri = ws_dir / "anysphere.cursor-retri"
        
        if cursor_retri.exists():
            print(f"\n=== Workspace: {ws_dir.name} ===")
            print(f"Cursor-retri directory: {cursor_retri}")
            
            # Check workspace.json to identify the workspace
            ws_json = ws_dir / "workspace.json"
            if ws_json.exists():
                try:
                    with open(ws_json, 'r', encoding='utf-8') as f:
                        ws_data = json.load(f)
                        if 'folder' in ws_data:
                            print(f"Workspace folder: {ws_data['folder']}")
                        if 'folderUri' in ws_data:
                            print(f"Workspace URI: {ws_data['folderUri']}")
                except Exception as e:
                    print(f"Could not read workspace.json: {e}")
            
            # List all files in cursor-retri
            try:
                all_files = list(cursor_retri.rglob("*"))
                print(f"Files in cursor-retri: {len(all_files)}")
                
                # Look for JSON files that might contain chat data
                json_files = list(cursor_retri.rglob("*.json"))
                print(f"JSON files found: {len(json_files)}")
                
                # Look for files with "chat" in name
                chat_files = [f for f in all_files if 'chat' in f.name.lower()]
                if chat_files:
                    print(f"Chat-related files: {len(chat_files)}")
                    for cf in chat_files[:5]:  # Show first 5
                        print(f"  - {cf.relative_to(cursor_retri)}")
                
                # Look for database files
                db_files = list(cursor_retri.rglob("*.db")) + list(cursor_retri.rglob("*.sqlite"))
                if db_files:
                    print(f"Database files: {len(db_files)}")
                    for db in db_files:
                        print(f"  - {db.relative_to(cursor_retri)} ({db.stat().st_size} bytes)")
                
                # Look for files with "Building" in name (your chat name)
                building_files = [f for f in all_files if 'building' in f.name.lower()]
                if building_files:
                    print(f"\n*** FILES WITH 'BUILDING' IN NAME (YOUR CHAT?): {len(building_files)} ***")
                    for bf in building_files:
                        print(f"  - {bf.relative_to(cursor_retri)}")
                        print(f"    Size: {bf.stat().st_size} bytes")
                        print(f"    Modified: {bf.stat().st_mtime}")
                
                # Check for storage.json or similar
                storage_files = [f for f in json_files if 'storage' in f.name.lower() or 'state' in f.name.lower()]
                if storage_files:
                    print(f"\nStorage/State files: {len(storage_files)}")
                    for sf in storage_files:
                        print(f"  - {sf.relative_to(cursor_retri)}")
                        try:
                            with open(sf, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, dict):
                                    print(f"    Keys: {list(data.keys())[:10]}")
                        except:
                            pass
            except Exception as e:
                print(f"Error reading cursor-retri: {e}")
        
        # Also check the workspace directory itself for any files
        all_ws_files = list(ws_dir.rglob("*"))
        building_ws_files = [f for f in all_ws_files if 'building' in f.name.lower() and f.is_file()]
        if building_ws_files:
            print(f"\n*** FILES WITH 'BUILDING' IN WORKSPACE DIRECTORY: {len(building_ws_files)} ***")
            for bf in building_ws_files:
                print(f"  - {bf.relative_to(ws_dir)}")
                print(f"    Size: {bf.stat().st_size} bytes")

def check_global_storage():
    """Check global storage for chat data"""
    appdata = os.getenv('APPDATA')
    global_storage = Path(appdata) / "Cursor" / "User" / "globalStorage"
    
    if not global_storage.exists():
        print("\n\n=== Global Storage not found ===")
        return
    
    print("\n\n=== Checking Global Storage ===")
    
    # Look for cursor-specific storage
    cursor_dirs = [d for d in global_storage.iterdir() if 'cursor' in d.name.lower()]
    for cd in cursor_dirs:
        print(f"\nFound: {cd.name}")
        json_files = list(cd.rglob("*.json"))
        if json_files:
            print(f"  JSON files: {len(json_files)}")
            for jf in json_files[:5]:
                print(f"    - {jf.name}")
        
        # Look for building-related files
        building_files = [f for f in cd.rglob("*") if 'building' in f.name.lower()]
        if building_files:
            print(f"  *** BUILDING FILES: {len(building_files)} ***")
            for bf in building_files:
                print(f"    - {bf.name}")

def check_local_storage():
    """Check Local Storage and IndexedDB"""
    appdata = os.getenv('APPDATA')
    local_storage = Path(appdata) / "Cursor" / "Local Storage"
    
    print("\n\n=== Checking Local Storage ===")
    if local_storage.exists():
        print(f"Local Storage path: {local_storage}")
        # Look for leveldb or other storage
        leveldb_dirs = list(local_storage.rglob("*leveldb*"))
        if leveldb_dirs:
            print(f"LevelDB directories: {len(leveldb_dirs)}")
            for ld in leveldb_dirs:
                print(f"  - {ld}")
        
        # Look for any files with building
        building_files = [f for f in local_storage.rglob("*") if 'building' in f.name.lower() and f.is_file()]
        if building_files:
            print(f"*** BUILDING FILES IN LOCAL STORAGE: {len(building_files)} ***")
            for bf in building_files:
                print(f"  - {bf}")
    else:
        print("Local Storage directory not found")

def check_leveldb_for_chat():
    """Check LevelDB storage for chat data"""
    appdata = os.getenv('APPDATA')
    leveldb_path = Path(appdata) / "Cursor" / "Local Storage" / "leveldb"
    
    print("\n\n=== Checking LevelDB Storage ===")
    if leveldb_path.exists():
        print(f"LevelDB path: {leveldb_path}")
        # LevelDB files
        log_files = list(leveldb_path.glob("*.log"))
        manifest_files = list(leveldb_path.glob("MANIFEST*"))
        sst_files = list(leveldb_path.glob("*.sst"))
        
        print(f"LevelDB files found:")
        print(f"  - Log files: {len(log_files)}")
        print(f"  - Manifest files: {len(manifest_files)}")
        print(f"  - SST files: {len(sst_files)}")
        print(f"  - Total size: {sum(f.stat().st_size for f in leveldb_path.iterdir() if f.is_file()) / 1024 / 1024:.2f} MB")
        print("\nNote: LevelDB requires special tools to read. We'll check other locations first.")
    else:
        print("LevelDB directory not found")

def find_chat_by_name():
    """Specifically search for chat named 'Building a custom AI system poc'"""
    appdata = os.getenv('APPDATA')
    workspace_storage = Path(appdata) / "Cursor" / "User" / "workspaceStorage"
    
    print("\n\n=== Searching for 'Building a custom AI system poc' Chat ===")
    
    if not workspace_storage.exists():
        print("Workspace storage not found")
        return None
    
    target_chat = None
    workspace_dirs = [d for d in workspace_storage.iterdir() if d.is_dir()]
    
    for ws_dir in workspace_dirs:
        # Check workspace.json to see if this is our workspace
        ws_json = ws_dir / "workspace.json"
        workspace_path = None
        
        if ws_json.exists():
            try:
                with open(ws_json, 'r', encoding='utf-8') as f:
                    ws_data = json.load(f)
                    if 'folder' in ws_data:
                        workspace_path = ws_data['folder']
                    elif 'folderUri' in ws_data:
                        workspace_path = ws_data['folderUri'].replace('file:///', '').replace('/', '\\')
            except:
                pass
        
        # Check if this is our workspace
        is_our_workspace = False
        if workspace_path and 'train_ai_tamar_request' in workspace_path:
            is_our_workspace = True
            print(f"\n*** FOUND YOUR WORKSPACE: {ws_dir.name} ***")
            print(f"   Path: {workspace_path}")
        
        # Search for chat-related files
        cursor_retri = ws_dir / "anysphere.cursor-retri"
        if cursor_retri.exists():
            try:
                # Look for all files
                all_files = list(cursor_retri.rglob("*"))
                
                # Search for files containing "building" or chat-related
                building_files = [f for f in all_files if 'building' in f.name.lower()]
                chat_files = [f for f in all_files if 'chat' in f.name.lower() or 'conversation' in f.name.lower()]
                
                if building_files or (is_our_workspace and chat_files):
                    print(f"\n  Found in workspace: {ws_dir.name}")
                    if building_files:
                        print(f"  *** BUILDING-RELATED FILES: {len(building_files)} ***")
                        for bf in building_files:
                            size = bf.stat().st_size if bf.is_file() else 0
                            mtime = datetime.fromtimestamp(bf.stat().st_mtime) if bf.is_file() else None
                            print(f"    - {bf.relative_to(cursor_retri)}")
                            if bf.is_file():
                                print(f"      Size: {size} bytes ({size/1024:.2f} KB)")
                                print(f"      Modified: {mtime}")
                                
                                # Try to read JSON files
                                if bf.suffix == '.json':
                                    try:
                                        with open(bf, 'r', encoding='utf-8') as f:
                                            data = json.load(f)
                                            if isinstance(data, dict):
                                                print(f"      Keys: {list(data.keys())[:10]}")
                                                if 'title' in data or 'name' in data:
                                                    print(f"      Title/Name: {data.get('title') or data.get('name')}")
                                    except Exception as e:
                                        print(f"      (Could not read JSON: {e})")
                    
                    if is_our_workspace and chat_files:
                        print(f"  Chat-related files: {len(chat_files)}")
                        for cf in chat_files[:5]:
                            print(f"    - {cf.relative_to(cursor_retri)}")
                    
                    # Look for database files
                    db_files = [f for f in all_files if f.suffix in ['.db', '.sqlite']]
                    if db_files:
                        print(f"  Database files: {len(db_files)}")
                        for db in db_files:
                            size = db.stat().st_size
                            print(f"    - {db.relative_to(cursor_retri)} ({size/1024:.2f} KB)")
                
                # Check for storage.json or state.json
                storage_files = [f for f in cursor_retri.rglob("*.json") 
                               if 'storage' in f.name.lower() or 'state' in f.name.lower()]
                if storage_files and is_our_workspace:
                    print(f"\n  Storage/State files: {len(storage_files)}")
                    for sf in storage_files:
                        print(f"    - {sf.relative_to(cursor_retri)}")
                        try:
                            with open(sf, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, dict):
                                    print(f"      Top-level keys: {list(data.keys())[:15]}")
                                    # Look for chat-related keys
                                    chat_keys = [k for k in data.keys() if 'chat' in k.lower() or 'conversation' in k.lower()]
                                    if chat_keys:
                                        print(f"      *** CHAT-RELATED KEYS: {chat_keys} ***")
                        except Exception as e:
                            print(f"      (Could not read: {e})")
                            
            except Exception as e:
                print(f"  Error reading cursor-retri: {e}")
    
    return target_chat

if __name__ == "__main__":
    print("=" * 70)
    print("CURSOR CHAT DIAGNOSTIC - READ-ONLY SCAN")
    print("=" * 70)
    print("\nThis script only READS files - it makes NO changes to your system.")
    print("Safe for Cursor Pro Teams - only examines YOUR local storage.\n")
    
    find_cursor_chat_data()
    check_global_storage()
    check_local_storage()
    check_leveldb_for_chat()
    target_chat = find_chat_by_name()
    
    print("\n\n" + "=" * 70)
    print("=== DIAGNOSTIC COMPLETE ===")
    print("=" * 70)
    print("\nSummary:")
    print("- Scanned all Cursor workspace storage directories")
    print("- Checked global storage and local storage")
    print("- Searched specifically for 'Building a custom AI system poc'")
    print("\nNext steps:")
    print("1. Review the findings above")
    print("2. If chat files found: We can attempt recovery (Option 2)")
    print("3. If no files found: Chat may be lost or in cloud storage")
    print("4. If corrupted files found: We can try to repair them")
    print("\n" + "=" * 70)

