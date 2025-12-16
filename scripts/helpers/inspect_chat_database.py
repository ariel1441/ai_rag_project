#!/usr/bin/env python3
"""
READ-ONLY: Inspect state.vscdb to find chat entries
This script only READS - makes NO changes
"""
import os
import json
import sqlite3
from pathlib import Path
import shutil
from datetime import datetime

appdata = os.getenv('APPDATA')
workspace_id = '0cd3ede1a5c7331b4b8db62309a7af8c'
workspace_dir = Path(appdata) / "Cursor" / "User" / "workspaceStorage" / workspace_id
state_db = workspace_dir / "state.vscdb"

print("=" * 70)
print("READ-ONLY DATABASE INSPECTION")
print("=" * 70)
print("\n⚠️  IMPORTANT: Close Cursor before running this!")
print("   (Database may be locked if Cursor is running)\n")

if not state_db.exists():
    print(f"ERROR: Database not found at {state_db}")
    exit(1)

print(f"Database: {state_db}")
print(f"Size: {state_db.stat().st_size} bytes\n")

# Try to connect (will fail if locked)
try:
    # First, try to make a copy to avoid locking issues
    temp_db = workspace_dir / "state.vscdb.temp_inspect"
    print("Creating temporary copy to avoid locking issues...")
    shutil.copy2(state_db, temp_db)
    print("✓ Copy created\n")
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    
    print("=" * 70)
    print("INSPECTING ItemTable")
    print("=" * 70)
    
    # Get all rows from ItemTable
    cursor.execute("SELECT * FROM ItemTable")
    rows = cursor.fetchall()
    
    print(f"\nTotal rows: {len(rows)}")
    print(f"Columns: {[description[0] for description in cursor.description]}\n")
    
    # Look for chat-related entries
    chat_entries = []
    building_entries = []
    all_entries = []
    
    for row in rows:
        row_dict = {}
        for i, col in enumerate(cursor.description):
            row_dict[col[0]] = row[i]
        
        all_entries.append(row_dict)
        
        # Convert values to string for searching
        row_str = str(row).lower()
        
        # Look for chat-related keywords
        if any(keyword in row_str for keyword in ['chat', 'conversation', 'message', 'requestid']):
            chat_entries.append(row_dict)
        
        # Look for "building" keyword
        if 'building' in row_str:
            building_entries.append(row_dict)
    
    print(f"\n📊 Summary:")
    print(f"  - Total entries: {len(all_entries)}")
    print(f"  - Chat-related entries: {len(chat_entries)}")
    print(f"  - 'Building' keyword found: {len(building_entries)}")
    
    # Show chat-related entries
    if chat_entries:
        print("\n" + "=" * 70)
        print("CHAT-RELATED ENTRIES")
        print("=" * 70)
        for i, entry in enumerate(chat_entries, 1):
            print(f"\n--- Entry {i} ---")
            for key, value in entry.items():
                # Truncate long values
                if isinstance(value, str) and len(value) > 200:
                    display_value = value[:200] + "... (truncated)"
                else:
                    display_value = value
                print(f"  {key}: {display_value}")
            
            # Try to parse JSON if value looks like JSON
            for key, value in entry.items():
                if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, dict):
                            # Look for chat-related keys
                            chat_keys = [k for k in parsed.keys() if 'chat' in str(k).lower() or 
                                       'conversation' in str(k).lower() or 
                                       'request' in str(k).lower() or
                                       'building' in str(k).lower()]
                            if chat_keys:
                                print(f"    *** Contains chat-related keys: {chat_keys} ***")
                                # Show relevant values
                                for ck in chat_keys:
                                    print(f"      {ck}: {parsed[ck]}")
                    except:
                        pass
    
    # Show building-related entries
    if building_entries:
        print("\n" + "=" * 70)
        print("'BUILDING' KEYWORD ENTRIES")
        print("=" * 70)
        for i, entry in enumerate(building_entries, 1):
            print(f"\n--- Entry {i} ---")
            for key, value in entry.items():
                if isinstance(value, str) and len(value) > 200:
                    display_value = value[:200] + "... (truncated)"
                else:
                    display_value = value
                print(f"  {key}: {display_value}")
    
    # Show sample of all entries (first 5)
    print("\n" + "=" * 70)
    print("SAMPLE ENTRIES (First 5)")
    print("=" * 70)
    for i, entry in enumerate(all_entries[:5], 1):
        print(f"\n--- Entry {i} ---")
        for key, value in entry.items():
            if isinstance(value, str) and len(value) > 150:
                display_value = value[:150] + "... (truncated)"
            else:
                display_value = value
            print(f"  {key}: {display_value}")
    
    # Check cursorDiskKV table
    print("\n" + "=" * 70)
    print("CHECKING cursorDiskKV TABLE")
    print("=" * 70)
    cursor.execute("SELECT COUNT(*) FROM cursorDiskKV")
    count = cursor.fetchone()[0]
    print(f"Rows: {count}")
    if count > 0:
        cursor.execute("SELECT * FROM cursorDiskKV LIMIT 10")
        kv_rows = cursor.fetchall()
        print("Sample entries:")
        for row in kv_rows:
            print(f"  {row}")
    
    conn.close()
    
    # Clean up temp file
    if temp_db.exists():
        temp_db.unlink()
        print("\n✓ Temporary copy cleaned up")
    
    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    if chat_entries or building_entries:
        print("✓ Found chat-related entries!")
        print("  - Review the entries above")
        print("  - Look for broken references or missing IDs")
        print("  - We can attempt repair if corruption is found")
    else:
        print("⚠️  No obvious chat entries found in ItemTable")
        print("  - Chat might be stored differently")
        print("  - Or metadata might be in a different format")
        print("  - May need to check cloud storage status")
    
except sqlite3.OperationalError as e:
    if "locked" in str(e).lower():
        print("\n❌ ERROR: Database is locked!")
        print("   Please close Cursor completely and try again.")
        print("   (Cursor must be fully closed, not just minimized)")
    else:
        print(f"\n❌ ERROR: {e}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Clean up temp file if it exists
    temp_db = workspace_dir / "state.vscdb.temp_inspect"
    if temp_db.exists():
        try:
            temp_db.unlink()
        except:
            pass








