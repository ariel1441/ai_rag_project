"""Test with manually corrected name to see if retrieval works"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.rag_query import RAGSystem
from scripts.utils.hebrew import fix_hebrew_rtl

rag = RAGSystem()
rag.connect_db()

# Test with CORRECT name (bypassing parser issue)
print("="*80)
print("TEST: Using CORRECT name 'יניב ליבוביץ' directly")
print("="*80)
print()

# Manually create query that will work
query = "פניות מיניב ליבוביץ"  # Using "מ" prefix to match pattern

print(f"Query: {fix_hebrew_rtl(query)}")
print()

# Use retrieve_requests directly with a query that should work
# Actually, let's test with the exact name in the query
test_query = "יניב ליבוביץ"  # Just the name

print("Testing retrieval with query: 'יניב ליבוביץ'")
print()

requests = rag.retrieve_requests(test_query, top_k=20)

print(f"Retrieved: {len(requests)} requests")
print()
print("Top 10 Retrieved Requests:")
for i, req in enumerate(requests[:10], 1):
    print(f"  {i}. Request {req['requestid']}")
    if req.get('updatedby'):
        print(f"     Updated By: {fix_hebrew_rtl(str(req['updatedby']))}")
    if req.get('projectname'):
        print(f"     Project: {fix_hebrew_rtl(str(req['projectname']))}")
    print(f"     Similarity: {req.get('similarity', 0):.4f}")
    print()

# Check if we found the expected IDs
expected_ids = ['211000001', '211000002', '211000003', '211000004', '211000272']
retrieved_ids = [str(r['requestid']) for r in requests]
matching = [rid for rid in retrieved_ids if rid in expected_ids]

print(f"Expected IDs from CSV: {expected_ids}")
print(f"Found matching: {matching}")
print(f"Match count: {len(matching)}/{len(expected_ids)}")

rag.close()

