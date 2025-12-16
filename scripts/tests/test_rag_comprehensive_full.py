"""
Comprehensive RAG Test - Full System with LLM
Tests multiple query types, speed, and accuracy
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.rag_query import RAGSystem
from scripts.utils.hebrew import fix_hebrew_rtl
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection for verification"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5433')),
        database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

def count_requests_by_name(db_conn, name):
    """Count requests by person name from database"""
    cursor = db_conn.cursor()
    # Search in updatedby field
    cursor.execute(
        "SELECT COUNT(*) FROM requests WHERE updatedby = %s",
        (name,)
    )
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def count_requests_by_type(db_conn, type_id):
    """Count requests by type from database"""
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM requests WHERE typeid = %s",
        (type_id,)
    )
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def get_sample_request_ids(db_conn, name, limit=5):
    """Get sample request IDs for a person name"""
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT requestid FROM requests WHERE updatedby = %s LIMIT %s",
        (name, limit)
    )
    ids = [str(row[0]) for row in cursor.fetchall()]
    cursor.close()
    return ids

# Test queries
test_queries = [
    {
        'query': 'כמה פניות יש מיניב ליבוביץ?',
        'type': 'count',
        'expected_name': 'יניב ליבוביץ',
        'description': 'Count requests by person name'
    },
    {
        'query': 'כמה פניות יש מאור גלילי?',
        'type': 'count',
        'expected_name': 'אור גלילי',
        'description': 'Count requests by person name (מא pattern)'
    },
    {
        'query': 'כמה בקשות יש מסוג 1?',
        'type': 'count_type',
        'expected_type': 1,
        'description': 'Count requests by type'
    },
    {
        'query': 'תביא לי פניות מאוקסנה כלפון',
        'type': 'find',
        'expected_name': 'אוקסנה כלפון',
        'description': 'Find requests by person name'
    },
    {
        'query': 'כמה פניות יש מסוג 2?',
        'type': 'count_type',
        'expected_type': 2,
        'description': 'Count requests by type 2'
    },
]

print("="*80)
print("COMPREHENSIVE RAG TEST - FULL SYSTEM")
print("="*80)
print()

# Connect to database for verification
print("Connecting to database...")
db_conn = get_db_connection()
print("✅ Database connected")
print()

# Initialize RAG system
print("Initializing RAG system...")
print("(This will load the LLM model - first time is slow)")
print()

start_init = time.time()
rag = RAGSystem()
rag.connect_db()
init_time = time.time() - start_init

print(f"✅ RAG system initialized in {init_time:.2f} seconds")
print()

# Test queries
results = []

for i, test in enumerate(test_queries, 1):
    print("="*80)
    print(f"TEST {i}/{len(test_queries)}: {test['description']}")
    print("="*80)
    print(f"Query: {fix_hebrew_rtl(test['query'])}")
    print()
    
    # Get expected result from database
    if test['type'] == 'count':
        expected_count = count_requests_by_name(db_conn, test['expected_name'])
        expected_samples = get_sample_request_ids(db_conn, test['expected_name'], 5)
        print(f"Expected from DB: {expected_count} requests")
        print(f"Sample IDs: {expected_samples[:5]}")
    elif test['type'] == 'count_type':
        expected_count = count_requests_by_type(db_conn, test['expected_type'])
        print(f"Expected from DB: {expected_count} requests (type {test['expected_type']})")
    elif test['type'] == 'find':
        expected_count = count_requests_by_name(db_conn, test['expected_name'])
        expected_samples = get_sample_request_ids(db_conn, test['expected_name'], 5)
        print(f"Expected from DB: {expected_count} requests")
        print(f"Sample IDs: {expected_samples[:5]}")
    
    print()
    
    # Run RAG query
    print("Running RAG query...")
    query_start = time.time()
    
    try:
        result = rag.query(test['query'])
        query_time = time.time() - query_start
        
        # Extract answer and retrieved requests
        answer = result.get('answer', '') if isinstance(result, dict) else str(result)
        retrieved_requests = result.get('requests', []) if isinstance(result, dict) else []
        
        print(f"✅ Query completed in {query_time:.2f} seconds")
        print()
        print("RAG Answer:")
        print("-"*80)
        print(fix_hebrew_rtl(answer))
        print("-"*80)
        print()
        
        # Compare with expected
        if test['type'] in ['count', 'find']:
            print(f"Retrieved {len(retrieved_requests)} requests")
            if retrieved_requests:
                retrieved_ids = [str(r.get('requestid', '')) for r in retrieved_requests[:10]]
                print(f"Sample retrieved IDs: {retrieved_ids[:5]}")
                if 'expected_samples' in locals() and expected_samples:
                    matching = [rid for rid in retrieved_ids if rid in expected_samples]
                    print(f"Matching with expected: {len(matching)}/{len(expected_samples[:5])}")
        print()
        
        results.append({
            'test': test,
            'answer': answer,
            'retrieved_requests': retrieved_requests,
            'query_time': query_time,
            'expected_count': expected_count if 'expected_count' in locals() else None,
            'expected_samples': expected_samples if 'expected_samples' in locals() else None,
            'success': True
        })
        
    except Exception as e:
        query_time = time.time() - query_start
        print(f"❌ Query failed after {query_time:.2f} seconds")
        print(f"Error: {e}")
        print()
        
        results.append({
            'test': test,
            'answer': None,
            'query_time': query_time,
            'error': str(e),
            'success': False
        })
    
    print()

# Summary
print("="*80)
print("TEST SUMMARY")
print("="*80)
print()

print(f"Initialization time: {init_time:.2f} seconds")
print()

total_query_time = sum(r['query_time'] for r in results if r['success'])
avg_query_time = total_query_time / len([r for r in results if r['success']]) if results else 0

print(f"Total query time: {total_query_time:.2f} seconds")
print(f"Average query time: {avg_query_time:.2f} seconds")
print(f"Number of successful queries: {len([r for r in results if r['success']])}/{len(results)}")
print()

# Close connections
rag.close()
db_conn.close()

print("✅ All tests completed")
print()

# Save results to file
with open('test_results_full.txt', 'w', encoding='utf-8') as f:
    f.write("COMPREHENSIVE RAG TEST RESULTS\n")
    f.write("="*80 + "\n\n")
    f.write(f"Initialization time: {init_time:.2f} seconds\n")
    f.write(f"Average query time: {avg_query_time:.2f} seconds\n\n")
    
    for i, result in enumerate(results, 1):
        f.write(f"TEST {i}: {result['test']['description']}\n")
        f.write("-"*80 + "\n")
        f.write(f"Query: {result['test']['query']}\n")
        if result['success']:
            f.write(f"Answer: {result['answer']}\n")
            if result['expected_count'] is not None:
                f.write(f"Expected count: {result['expected_count']}\n")
            f.write(f"Query time: {result['query_time']:.2f} seconds\n")
        else:
            f.write(f"Error: {result.get('error', 'Unknown error')}\n")
        f.write("\n")

print("Results saved to test_results_full.txt")

