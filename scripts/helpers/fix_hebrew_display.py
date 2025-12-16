"""
Fix Hebrew display in PowerShell/CMD.
Run this before running other scripts to fix Hebrew display.
"""
import os
import sys

print("Fixing Hebrew display in terminal...")
print()

# Set console code page to UTF-8
if sys.platform == 'win32':
    try:
        # Method 1: Set code page
        os.system('chcp 65001 >nul 2>&1')
        print("✓ Set console code page to UTF-8 (65001)")
        
        # Method 2: Set output encoding
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            print("✓ Reconfigured stdout to UTF-8")
        
        # Test Hebrew display
        print()
        print("Hebrew test: אלינור בדיקה")
        print("If you see Hebrew correctly above, the fix worked!")
        print()
        print("NOTE: This fix only works for this terminal session.")
        print("For permanent fix, see docs/FIX_HEBREW_CURSOR.md")
        
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Manual fix:")
        print("  1. Run: chcp 65001")
        print("  2. Or use Windows Terminal (better Hebrew support)")
else:
    print("This script is for Windows only.")

