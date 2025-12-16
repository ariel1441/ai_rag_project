"""Test Hebrew character positions for מאור"""
query = 'פניות מאור גלילי'
pattern = 'מא'

print(f"Query: {query}")
print(f"Query length: {len(query)}")
print()

# Find pattern
idx = query.find(pattern)
print(f"Pattern '{pattern}' found at position: {idx}")
print(f"Pattern length: {len(pattern)}")
print()

# Show characters around pattern
if idx != -1:
    after_idx = idx + len(pattern)
    print(f"After pattern (position {after_idx}): '{query[after_idx:]}'")
    print(f"Character at position {after_idx}: '{query[after_idx]}' (Unicode: U+{ord(query[after_idx]):04X})")
    print()
    
    # Show the word "מאור" character by character
    if idx + 4 <= len(query):
        word = query[idx:idx+4]  # "מאור"
        print(f"Word 'מאור' (positions {idx}-{idx+3}): '{word}'")
        for i, char in enumerate(word):
            print(f"  Position {idx+i}: '{char}' (U+{ord(char):04X})")
        print()
        
        # After "מא", we should get "אור"
        after_mem_alef = query[after_idx:]
        print(f"Text after 'מא': '{after_mem_alef}'")
        import re
        hebrew_words = re.findall(r'[\u0590-\u05FF]+', after_mem_alef)
        print(f"Hebrew words extracted: {hebrew_words}")
        print()
        
        # The issue: "מאור" is one word, so after "מא" we get "ור" (missing "א")
        # But we want "אור". The "א" is at position idx+1 (right after "מ")
        # So we need to check: if the character at idx+1 is "א", then the name starts with "א"
        char_after_mem = query[idx+1]  # Should be "א" in "מאור"
        print(f"Character after 'מ' (position {idx+1}): '{char_after_mem}' (U+{ord(char_after_mem):04X})")
        if char_after_mem == 'א':
            print("  → This is 'מא' + name starting with 'א'")
            print("  → Should extract name starting from 'א'")
            # The name is from position idx+1 onwards, but we need to find where it ends
            # In "מאור", the name "אור" is at positions idx+1 to idx+3
            name_start = idx + 1
            # Find end of Hebrew word
            name_end = name_start
            while name_end < len(query) and ('\u0590' <= query[name_end] <= '\u05FF'):
                name_end += 1
            name = query[name_start:name_end]
            print(f"  → Extracted name: '{name}'")

