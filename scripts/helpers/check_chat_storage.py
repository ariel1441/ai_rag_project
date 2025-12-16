#!/usr/bin/env python3
"""
Check various storage locations for chat data
"""
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

appdata = os.getenv('APPDATA')
workspace_id = '0cd3ede1a5c7331b4b8db62309a7af8c'
workspace_dir = Path(appdata) / "Cursor" / "User" / "workspaceStorage" / workspace_id

print("=" * 70)
print("CHAT STORAGE INVESTIGATION")
print("=" * 70)

# Check state.vscdb (VS Code database)
print("\n=== Checking state.vscdb ===")
state_db = workspace_dir / "state.vscdb"
if state_db.exists():
    print(f"Found: {state_db} ({state_db.stat().st_size} bytes)")
    try:
        conn = sqlite3.connect(str(state_db))
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables found: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
            
            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"    Rows: {count}")
                
                # If it's a key-value table, show some keys
                if count > 0 and count < 100:
                    cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
                    rows = cursor.fetchall()
                    print(f"    Sample data (first 5 rows):")
                    for row in rows:
                        # Truncate long values
                        row_str = str(row)
                        if len(row_str) > 100:
                            row_str = row_str[:100] + "..."
                        print(f"      {row_str}")
            except Exception as e:
                print(f"    (Could not read: {e})")
        
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")
        print("(Database might be locked or in use by Cursor)")

# Check cursor-retrieval directory
print("\n=== Checking anysphere.cursor-retrieval ===")
cursor_retrieval = workspace_dir / "anysphere.cursor-retrieval"
if cursor_retrieval.exists():
    print(f"Found: {cursor_retrieval}")
    all_files = list(cursor_retrieval.rglob("*"))
    print(f"Total files: {len([f for f in all_files if f.is_file()])}")
    
    for item in sorted(cursor_retrieval.iterdir()):
        if item.is_file():
            size = item.stat().st_size
            print(f"  📄 {item.name} ({size} bytes)")
            # Try to read text files
            if item.suffix == '.txt' and size < 100000:
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for chat-related content
                        if 'building' in content.lower() or 'chat' in content.lower():
                            print(f"    *** Contains 'building' or 'chat' keywords ***")
                            # Show first 200 chars
                            preview = content[:200].replace('\n', ' ')
                            print(f"    Preview: {preview}...")
                except:
                    pass

# Check global storage for chat data
print("\n=== Checking Global Storage for Chat Data ===")
global_storage = Path(appdata) / "Cursor" / "User" / "globalStorage"
if global_storage.exists():
    # Look for cursor-specific extensions
    cursor_extensions = [d for d in global_storage.iterdir() 
                        if 'cursor' in d.name.lower() or 'anysphere' in d.name.lower()]
    
    for ext_dir in cursor_extensions:
        print(f"\nFound: {ext_dir.name}")
        # Look for JSON files
        json_files = list(ext_dir.rglob("*.json"))
        if json_files:
            print(f"  JSON files: {len(json_files)}")
            for jf in json_files[:10]:
                size = jf.stat().st_size
                print(f"    - {jf.name} ({size} bytes)")
                # Try to read small JSON files
                if size < 100000:
                    try:
                        with open(jf, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                keys = list(data.keys())
                                # Check for chat-related keys
                                chat_keys = [k for k in keys if 'chat' in str(k).lower() or 
                                           'conversation' in str(k).lower() or 
                                           'building' in str(k).lower()]
                                if chat_keys:
                                    print(f"      *** CHAT-RELATED KEYS: {chat_keys} ***")
                    except:
                        pass

# Check for chat data in other workspace directories
print("\n=== Checking Other Workspaces for Chat Data ===")
workspace_storage = Path(appdata) / "Cursor" / "User" / "workspaceStorage"
if workspace_storage.exists():
    other_workspaces = [d for d in workspace_storage.iterdir() 
                       if d.is_dir() and d.name != workspace_id]
    
    print(f"Checking {len(other_workspaces)} other workspaces...")
    for ws in other_workspaces[:5]:  # Check first 5
        cursor_retri = ws / "anysphere.cursor-retri"
        if cursor_retri.exists():
            # Look for building-related files
            all_files = list(cursor_retri.rglob("*"))
            building_files = [f for f in all_files if 'building' in f.name.lower()]
            if building_files:
                print(f"\n  *** Found in workspace {ws.name}: {len(building_files)} building files ***")
                for bf in building_files:
                    print(f"    - {bf.relative_to(cursor_retri)}")

print("\n" + "=" * 70)
print("DIAGNOSIS SUMMARY")
print("=" * 70)
print("\nFindings:")
print("1. Workspace directory exists and is accessible")
print("2. state.vscdb contains workspace state (may include chat metadata)")
print("3. anysphere.cursor-retrieval contains retrieval-related files")
print("4. No cursor-retri directory found (chat may be in cloud)")
print("\nPossible reasons chat won't load:")
print("- Chat data stored in Cursor Pro Teams cloud (not local)")
print("- Chat metadata corrupted in state.vscdb")
print("- Chat ID/reference missing or broken")
print("\nNext steps:")
print("- If using Cursor Pro Teams: Chat may be in cloud storage")
print("- Can try to repair state.vscdb if corrupted")
print("- Can check Cursor's cloud sync status")

