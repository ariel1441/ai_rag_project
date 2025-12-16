"""Test the query parser with example queries."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.query_parser import parse_query

print("=" * 80)
print("QUERY PARSER TEST")
print("=" * 80)
print()

test_queries = [
    "פניות מאור גלילי",
    "בקשות מסוג 4",
    "פרויקט אלינור",
    "תביא לי פניות מיניב ליבוביץ",
    "כמה פניות יש מאור גלילי",
    "Show me requests where ResponsibleEmployeeName is יניב ליבוביץ"
]

for query in test_queries:
    result = parse_query(query)
    print(f"Query: {query}")
    print(f"  Intent: {result['intent']}")
    print(f"  Entities: {result['entities']}")
    print(f"  Target fields: {result['target_fields'][:3] if result['target_fields'] else 'None'}")
    print(f"  Query type: {result['query_type']}")
    print()

print("=" * 80)

