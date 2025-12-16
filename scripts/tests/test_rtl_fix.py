"""
Test RTL fix function.
"""
import re

def fix_hebrew_rtl(text):
    """Fix Hebrew RTL display for LTR terminals."""
    if not text:
        return text
    pattern = r'([\u0590-\u05FF]+|[^\u0590-\u05FF]+)'
    parts = re.findall(pattern, str(text))
    result = []
    for part in parts:
        if re.match(r'[\u0590-\u05FF]+', part):
            result.append(part[::-1])
        else:
            result.append(part)
    return ''.join(result)

# Test
test_cases = [
    "אלינור",
    "Project: אלינור בדיקה",
    "אלינור ירדן - חיצוני",
    "בנית בנין"
]

print("=" * 70)
print("RTL Fix Test")
print("=" * 70)
print()

for original in test_cases:
    fixed = fix_hebrew_rtl(original)
    print(f"Original: {original}")
    print(f"Fixed:    {fixed}")
    print(f"Bytes:    {original.encode('utf-8').hex()[:50]}...")
    print()

print("=" * 70)
print("If 'Fixed' shows Hebrew correctly, the function works!")
print("=" * 70)

