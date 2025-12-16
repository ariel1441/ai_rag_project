"""Debug name extraction to understand the issue"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from utils.query_parser import parse_query
import re

queries = [
    "כמה פניות יש מיניב ליבוביץ?",
    "תביא לי פניות מיניב ליבוביץ",
    "פניות מאור גלילי",
    "כמה פניות יש מאוקסנה כלפון?",
]

print("="*80)
print("DEBUGGING NAME EXTRACTION")
print("="*80)

for query in queries:
    print(f"\nQuery: {query}")
    print("-"*80)
    
    # Show what patterns are found
    query_lower = query.lower()
    patterns = ['מא', 'של', 'על ידי', 'מאת', 'מ-']
    print("Pattern matching:")
    for pattern in patterns:
        idx = query_lower.find(pattern)
        if idx != -1:
            print(f"  '{pattern}' found at position {idx}")
            if idx + len(pattern) < len(query):
                next_char = query[idx + len(pattern)]
                print(f"    Next char: '{next_char}' (Hebrew: {ord(next_char) >= 0x0590 and ord(next_char) <= 0x05FF})")
    
    # Show Hebrew words
    hebrew_words = re.findall(r'[\u0590-\u05FF]+', query)
    print(f"Hebrew words: {hebrew_words}")
    
    # Parse
    result = parse_query(query)
    print(f"Extracted name: {result['entities'].get('person_name', 'None')}")
    print(f"Expected: Should match database names")
    print()

