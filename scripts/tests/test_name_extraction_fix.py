"""Test name extraction fix"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from utils.query_parser import parse_query

queries = [
    "כמה פניות יש מיניב ליבוביץ?",
    "תביא לי פניות מיניב ליבוביץ",
    "פניות מאור גלילי",
    "כמה פניות יש מאוקסנה כלפון?",
]

print("Testing name extraction:")
print("="*80)

for query in queries:
    result = parse_query(query)
    person_name = result['entities'].get('person_name', 'None')
    print(f"\nQuery: {query}")
    print(f"Intent: {result['intent']}")
    print(f"Extracted name: {person_name}")
    print(f"Expected: Should be correct Hebrew name (not with extra 'מ')")

