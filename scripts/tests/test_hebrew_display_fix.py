"""
Test and fix Hebrew display in terminal.
"""
import os
import sys

print("Testing Hebrew display fix...")
print()

# Method 1: Set code page
if sys.platform == 'win32':
    try:
        # Set UTF-8 code page
        result = os.system('chcp 65001 >nul 2>&1')
        if result == 0:
            print("✓ Set code page to UTF-8 (65001)")
        else:
            print("⚠ Could not set code page")
    except:
        pass

# Method 2: Reconfigure stdout
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        print("✓ Reconfigured stdout to UTF-8")
    else:
        # Fallback for older Python
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        print("✓ Set stdout encoding to UTF-8 (codecs)")
except Exception as e:
    print(f"⚠ Could not reconfigure stdout: {e}")

# Method 3: Set environment variable
os.environ['PYTHONIOENCODING'] = 'utf-8'

print()
print("=" * 70)
print("Hebrew Display Test")
print("=" * 70)
print()

# Test Hebrew
test_texts = [
    "אלינור",
    "אלינור בדיקה",
    "בנית בנין",
    "בקשות מסוג 4",
    "תביא לי את כל הפניות שקשורות לבניה"
]

print("If Hebrew displays correctly below, the fix worked:")
print()
for text in test_texts:
    print(f"  {text}")
    print()

print("=" * 70)
print()
print("If Hebrew still displays backwards:")
print("  1. Use Windows Terminal (better support)")
print("  2. Or run: chcp 65001 in terminal before scripts")
print("  3. Or set Cursor to use Windows Terminal as default")
print()

