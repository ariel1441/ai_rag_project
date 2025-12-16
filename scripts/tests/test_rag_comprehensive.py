"""
Comprehensive RAG Test Script
Tests all RAG query types with GPU-optimized system.

This script tests:
1. Find queries (person, project, type, status)
2. Count queries
3. Summarize queries
4. Similar requests queries
5. Date-based queries
6. Urgency queries
7. Answer retrieval queries
8. Complex multi-entity queries

Uses GPU-optimized RAG system for fast, high-quality answers.
"""
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

# Try to load dotenv (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import GPU-optimized RAG system
from scripts.core.rag_query_gpu import GPUOptimizedRAGSystem

print("=" * 80)
print("COMPREHENSIVE RAG TEST SUITE")
print("=" * 80)
print()
print("Testing all RAG query types with GPU-optimized system")
print("This will verify that RAG works correctly and uses GPU for fast responses")
print()

# Initialize RAG system
print("Initializing RAG system...")
print("  (This will load the LLM model - may take 1-2 minutes on first run)")
print()

rag_system = GPUOptimizedRAGSystem()

# Check GPU
import torch
if torch.cuda.is_available():
    print(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
    print(f"  CUDA version: {torch.version.cuda}")
    print(f"  GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("⚠️  No GPU detected - will use CPU (slower)")
print()

# Test queries organized by type
test_queries: List[Tuple[str, str, Dict]] = [
    # ========================================================================
    # FIND QUERIES (Person, Project, Type, Status)
    # ========================================================================
    ("find_person", "פניות מאור גלילי", {
        "expected_intent": "person",
        "expected_entity": "אור גלילי",
        "description": "Find requests by person name"
    }),
    ("find_person", "בקשות מיניב ליבוביץ", {
        "expected_intent": "person",
        "expected_entity": "יניב ליבוביץ",
        "description": "Find requests by person name (alternative name)"
    }),
    ("find_project", "פניות מפרויקט אלינור", {
        "expected_intent": "project",
        "description": "Find requests by project name"
    }),
    ("find_type", "פניות מסוג 4", {
        "expected_intent": "type",
        "expected_type_id": 4,
        "description": "Find requests by type ID"
    }),
    ("find_status", "בקשות בסטטוס 1", {
        "expected_intent": "status",
        "expected_status_id": 1,
        "description": "Find requests by status ID"
    }),
    ("find_multi", "פניות מאור גלילי מסוג 10", {
        "expected_intent": "person",
        "expected_entity": "אור גלילי",
        "expected_type_id": 10,
        "description": "Find requests with multiple filters (person + type)"
    }),
    
    # ========================================================================
    # COUNT QUERIES
    # ========================================================================
    ("count", "כמה פניות יש מאור גלילי?", {
        "expected_intent": "person",
        "expected_entity": "אור גלילי",
        "description": "Count requests by person"
    }),
    ("count", "כמה בקשות יש מסוג 4?", {
        "expected_intent": "type",
        "expected_type_id": 4,
        "description": "Count requests by type"
    }),
    ("count", "כמה פרויקטים יש לאור גלילי?", {
        "expected_intent": "person",
        "expected_entity": "אור גלילי",
        "description": "Count projects (not requests) by person"
    }),
    
    # ========================================================================
    # SUMMARIZE QUERIES
    # ========================================================================
    ("summarize", "תביא לי סיכום של כל הפניות מסוג 4", {
        "expected_intent": "type",
        "expected_type_id": 4,
        "description": "Summarize requests by type"
    }),
    ("summarize", "תן לי סיכום של פניות מאור גלילי", {
        "expected_intent": "person",
        "expected_entity": "אור גלילי",
        "description": "Summarize requests by person"
    }),
    
    # ========================================================================
    # SIMILAR REQUESTS QUERIES
    # ========================================================================
    ("similar", "תביא לי פניות דומות ל-211000001", {
        "expected_request_id": "211000001",
        "description": "Find similar requests by ID"
    }),
    ("similar", "פניות דומות ל-211000226", {
        "expected_request_id": "211000226",
        "description": "Find similar requests (alternative format)"
    }),
    
    # ========================================================================
    # DATE-BASED QUERIES
    # ========================================================================
    ("date", "פניות מחודש האחרון", {
        "description": "Find requests from last month"
    }),
    ("date", "בקשות מ-2024", {
        "description": "Find requests from year 2024"
    }),
    
    # ========================================================================
    # URGENCY QUERIES
    # ========================================================================
    ("urgent", "בקשות דחופות", {
        "expected_urgency": True,
        "description": "Find urgent requests"
    }),
    ("urgent", "פניות דחופות מאור גלילי", {
        "expected_intent": "person",
        "expected_entity": "אור גלילי",
        "expected_urgency": True,
        "description": "Find urgent requests by person"
    }),
    
    # ========================================================================
    # ANSWER RETRIEVAL QUERIES
    # ========================================================================
    ("answer_retrieval", "מה התשובה שניתנה לפנייה 211000001?", {
        "expected_request_id": "211000001",
        "description": "Retrieve answer from similar requests"
    }),
    
    # ========================================================================
    # COMPLEX QUERIES
    # ========================================================================
    ("complex", "תביא לי סיכום של פניות דחופות מאור גלילי מסוג 10", {
        "expected_intent": "person",
        "expected_entity": "אור גלילי",
        "expected_type_id": 10,
        "expected_urgency": True,
        "description": "Complex query: person + type + urgency + summarize"
    }),
    ("complex", "כמה פניות יש מאור גלילי בסטטוס 1?", {
        "expected_intent": "person",
        "expected_entity": "אור גלילי",
        "expected_status_id": 1,
        "description": "Complex query: person + status + count"
    }),
    
    # ========================================================================
    # GENERAL SEMANTIC QUERIES
    # ========================================================================
    ("general", "פניות שקשורות לתכנון", {
        "description": "General semantic search"
    }),
    ("general", "בקשות עם בעיות", {
        "description": "General semantic search (problem-related)"
    }),
]

def test_single_query(query_type: str, query: str, metadata: Dict) -> Dict:
    """Test a single RAG query and return results."""
    print(f"Testing: {query}")
    print(f"  Type: {query_type}")
    print(f"  Description: {metadata.get('description', 'N/A')}")
    
    start_time = time.time()
    
    try:
        # Run RAG query
        result = rag_system.query(query)
        
        elapsed_time = time.time() - start_time
        
        # Extract information
        answer = result.get('answer', '')
        requests = result.get('requests', [])
        query_info = result.get('query_info', {})
        
        # Check if GPU was used
        import torch
        used_gpu = torch.cuda.is_available() and result.get('used_gpu', False)
        
        # Verify expectations if provided
        verification = {}
        if 'expected_intent' in metadata:
            actual_intent = query_info.get('intent', '')
            verification['intent_match'] = actual_intent == metadata['expected_intent']
        
        if 'expected_entity' in metadata:
            entities = query_info.get('entities', {})
            person_name = entities.get('person_name', '')
            verification['entity_match'] = metadata['expected_entity'] in person_name or person_name in metadata['expected_entity']
        
        return {
            'success': True,
            'query': query,
            'query_type': query_type,
            'answer': answer,
            'num_requests': len(requests),
            'query_info': query_info,
            'elapsed_time': elapsed_time,
            'used_gpu': used_gpu,
            'verification': verification,
            'error': None
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            'success': False,
            'query': query,
            'query_type': query_type,
            'answer': None,
            'num_requests': 0,
            'query_info': {},
            'elapsed_time': elapsed_time,
            'used_gpu': False,
            'verification': {},
            'error': str(e)
        }

def print_result(result: Dict):
    """Print formatted test result."""
    if result['success']:
        print(f"  ✓ Success ({result['elapsed_time']:.2f}s)")
        if result['used_gpu']:
            print(f"    GPU: ✓ Used")
        else:
            print(f"    GPU: ✗ Not used (CPU only)")
        print(f"    Requests found: {result['num_requests']}")
        print(f"    Answer length: {len(result['answer'])} chars")
        if result['answer']:
            print(f"    Answer preview: {result['answer'][:100]}...")
        
        # Verification results
        if result['verification']:
            for check, passed in result['verification'].items():
                status = "✓" if passed else "✗"
                print(f"    {status} {check}: {passed}")
    else:
        print(f"  ✗ Failed ({result['elapsed_time']:.2f}s)")
        print(f"    Error: {result['error']}")
    print()

# Run all tests
print("=" * 80)
print("RUNNING TESTS")
print("=" * 80)
print()

results = []
for query_type, query, metadata in test_queries:
    result = test_single_query(query_type, query, metadata)
    results.append(result)
    print_result(result)
    print("-" * 80)
    print()

# Summary
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print()

total_tests = len(results)
successful_tests = sum(1 for r in results if r['success'])
failed_tests = total_tests - successful_tests

print(f"Total tests: {total_tests}")
print(f"Successful: {successful_tests} ({successful_tests*100/total_tests:.1f}%)")
print(f"Failed: {failed_tests} ({failed_tests*100/total_tests:.1f}%)")
print()

# Timing statistics
if successful_tests > 0:
    successful_results = [r for r in results if r['success']]
    avg_time = sum(r['elapsed_time'] for r in successful_results) / len(successful_results)
    min_time = min(r['elapsed_time'] for r in successful_results)
    max_time = max(r['elapsed_time'] for r in successful_results)
    
    print(f"Timing (successful tests only):")
    print(f"  Average: {avg_time:.2f}s")
    print(f"  Min: {min_time:.2f}s")
    print(f"  Max: {max_time:.2f}s")
    print()
    
    # GPU usage
    gpu_used_count = sum(1 for r in successful_results if r['used_gpu'])
    print(f"GPU usage:")
    print(f"  Used GPU: {gpu_used_count}/{len(successful_results)} tests")
    print(f"  CPU only: {len(successful_results) - gpu_used_count}/{len(successful_results)} tests")
    print()

# Query type breakdown
print("Results by query type:")
query_type_counts = {}
for result in results:
    qtype = result['query_type']
    if qtype not in query_type_counts:
        query_type_counts[qtype] = {'total': 0, 'success': 0}
    query_type_counts[qtype]['total'] += 1
    if result['success']:
        query_type_counts[qtype]['success'] += 1

for qtype, counts in sorted(query_type_counts.items()):
    success_rate = counts['success'] * 100 / counts['total']
    print(f"  {qtype}: {counts['success']}/{counts['total']} ({success_rate:.1f}%)")
print()

# Failed tests details
if failed_tests > 0:
    print("Failed tests:")
    for result in results:
        if not result['success']:
            print(f"  ✗ {result['query']}")
            print(f"    Error: {result['error']}")
    print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print()
print("Next steps:")
print("1. Review the results above")
print("2. Check if GPU was used (should be faster)")
print("3. Verify answers make sense")
print("4. Test manually via web interface (see instructions)")
print()
