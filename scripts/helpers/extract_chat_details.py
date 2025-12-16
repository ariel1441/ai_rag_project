#!/usr/bin/env python3
"""
Extract and examine chat details from composer.composerData
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
print("EXTRACTING CHAT DETAILS")
print("=" * 70)

# Create temp copy
temp_db = workspace_dir / "state.vscdb.temp_extract"
shutil.copy2(state_db, temp_db)

conn = sqlite3.connect(str(temp_db))
cursor = conn.cursor()

# Get composer.composerData
cursor.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
result = cursor.fetchone()

if not result:
    print("ERROR: composer.composerData not found!")
    conn.close()
    temp_db.unlink()
    exit(1)

composer_data_str = result[0]
composer_data = json.loads(composer_data_str)

print("\n=== Composer Data Structure ===")
print(f"Keys: {list(composer_data.keys())}")

if 'allComposers' in composer_data:
    print(f"\nTotal composers (chats): {len(composer_data['allComposers'])}")
    
    print("\n" + "=" * 70)
    print("ALL CHATS FOUND")
    print("=" * 70)
    
    for i, composer in enumerate(composer_data['allComposers'], 1):
        print(f"\n--- Chat {i} ---")
        print(f"Type: {composer.get('type', 'N/A')}")
        print(f"Composer ID: {composer.get('composerId', 'N/A')}")
        print(f"Name: {composer.get('name', 'N/A')}")
        
        if 'createdAt' in composer:
            created = datetime.fromtimestamp(composer['createdAt'] / 1000)
            print(f"Created: {created}")
        
        if 'lastUpdatedAt' in composer:
            updated = datetime.fromtimestamp(composer['lastUpdatedAt'] / 1000)
            print(f"Last Updated: {updated}")
        
        # Check if this is the "Building" chat
        name = composer.get('name', '').lower()
        if 'building' in name or 'custom ai system' in name or 'poc' in name:
            print("*** THIS MIGHT BE YOUR CHAT! ***")
        
        # Show other keys
        other_keys = [k for k in composer.keys() if k not in ['type', 'composerId', 'name', 'createdAt', 'lastUpdatedAt']]
        if other_keys:
            print(f"Other fields: {other_keys}")

# Also check aiService.prompts for the "building" prompt
print("\n" + "=" * 70)
print("CHECKING PROMPTS (aiService.prompts)")
print("=" * 70)

cursor.execute("SELECT value FROM ItemTable WHERE key = 'aiService.prompts'")
result = cursor.fetchone()

if result:
    prompts_data = json.loads(result[0])
    print(f"Total prompts: {len(prompts_data)}")
    
    # Find prompts with "building" in them
    building_prompts = [p for p in prompts_data if 'building' in str(p).lower()]
    if building_prompts:
        print(f"\n*** Found {len(building_prompts)} prompt(s) with 'building' keyword ***")
        for i, prompt in enumerate(building_prompts, 1):
            print(f"\n--- Prompt {i} ---")
            if isinstance(prompt, dict):
                for key, value in prompt.items():
                    if isinstance(value, str) and len(value) > 300:
                        print(f"{key}: {value[:300]}... (truncated)")
                    else:
                        print(f"{key}: {value}")
            else:
                print(f"Prompt: {str(prompt)[:300]}...")

# Check aiService.generations
print("\n" + "=" * 70)
print("CHECKING GENERATIONS (aiService.generations)")
print("=" * 70)

cursor.execute("SELECT value FROM ItemTable WHERE key = 'aiService.generations'")
result = cursor.fetchone()

if result:
    generations_data = json.loads(result[0])
    print(f"Total generations: {len(generations_data)}")
    
    # Find generations with "building" in them
    building_gens = [g for g in generations_data if 'building' in str(g).lower()]
    if building_gens:
        print(f"\n*** Found {len(building_gens)} generation(s) with 'building' keyword ***")
        for i, gen in enumerate(building_gens[:3], 1):  # Show first 3
            print(f"\n--- Generation {i} ---")
            if isinstance(gen, dict):
                for key, value in gen.items():
                    if isinstance(value, str) and len(value) > 200:
                        print(f"{key}: {value[:200]}... (truncated)")
                    else:
                        print(f"{key}: {value}")

conn.close()
temp_db.unlink()

print("\n" + "=" * 70)
print("EXTRACTION COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Identify which composer ID corresponds to 'Building a custom AI system poc'")
print("2. Check if that composer has a broken reference")
print("3. Attempt to repair if possible")








