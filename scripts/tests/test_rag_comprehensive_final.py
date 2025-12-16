"""
Comprehensive RAG Test - Full System
Tests multiple query types, speed, accuracy, and design review.
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
    """Get database connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5433')),
        database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

def count_requests_in_db(conn, query_type, entity):
    """Count requests in database for verification."""
    cursor = conn.cursor()
    
    if query_type == 'person':
        # Count requests with person name in updatedby or createdby
        cursor.execute("""
            SELECT COUNT(DISTINCT requestid)
            FROM requests
            WHERE updatedby ILIKE %s OR createdby ILIKE %s
        """, (f'%{entity}%', f'%{entity}%'))
    elif query_type == 'type':
        # Count requests with type_id
        cursor.execute("""
            SELECT COUNT(DISTINCT requestid)
            FROM requests
            WHERE requesttypeid = %s
        """, (int(entity),))
    elif query_type == 'status':
        # Count requests with status_id
        cursor.execute("""
            SELECT COUNT(DISTINCT requestid)
            FROM requests
            WHERE requeststatusid = %s
        """, (int(entity),))
    else:
        return None
    
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def get_sample_ids(conn, query_type, entity, limit=5):
    """Get sample request IDs from database."""
    cursor = conn.cursor()
    
    if query_type == 'person':
        cursor.execute("""
            SELECT DISTINCT requestid
            FROM requests
            WHERE updatedby ILIKE %s OR createdby ILIKE %s
            ORDER BY requestid
            LIMIT %s
        """, (f'%{entity}%', f'%{entity}%', limit))
    elif query_type == 'type':
        cursor.execute("""
            SELECT DISTINCT requestid
            FROM requests
            WHERE requesttypeid = %s
            ORDER BY requestid
            LIMIT %s
        """, (int(entity), limit))
    elif query_type == 'status':
        cursor.execute("""
            SELECT DISTINCT requestid
            FROM requests
            WHERE requeststatusid = %s
            ORDER BY requestid
            LIMIT %s
        """, (int(entity), limit))
    else:
        return []
    
    ids = [str(row[0]) for row in cursor.fetchall()]
    cursor.close()
    return ids

def main():
    print("="*80)
    print("COMPREHENSIVE RAG TEST - FULL SYSTEM")
    print("="*80)
    print()
    
    # Connect to database
    print("Connecting to database...")
    db_conn = get_db_connection()
    print("✅ Database connected")
    print()
    
    # Initialize RAG system
    print("Initializing RAG system...")
    start_init = time.time()
    rag = RAGSystem()
    rag.connect_db()
    init_time = time.time() - start_init
    print(f"✅ RAG system initialized in {init_time:.2f} seconds")
    print()
    
    # Pre-load model (this is the slow part - only happens once)
    print("Pre-loading LLM model...")
    print("(This takes 30-60 seconds on first load, but only happens once)")
    print("(Subsequent queries will be fast - 5-15 seconds each)")
    print()
    
    start_model_load = time.time()
    rag.load_model()  # Load model upfront
    model_load_time = time.time() - start_model_load
    print(f"✅ Model loaded in {model_load_time:.2f} seconds")
    print("(Subsequent queries will be much faster)")
    print()
    
    # Test queries
    test_queries = [
        {
            'query': 'כמה פניות יש מאור גלילי?',
            'type': 'person',
            'entity': 'אור גלילי',
            'description': 'Count requests by person name'
        },
        {
            'query': 'כמה בקשות יש מסוג 1?',
            'type': 'type',
            'entity': 1,
            'description': 'Count requests by type'
        },
        {
            'query': 'תביא לי פניות מיניב ליבוביץ',
            'type': 'person',
            'entity': 'יניב ליבוביץ',
            'description': 'Find requests by person name'
        },
        {
            'query': 'כמה פניות יש מאוקסנה כלפון?',
            'type': 'person',
            'entity': 'אוקסנה כלפון',
            'description': 'Count requests by person name (another person)'
        },
        {
            'query': 'מה הפרויקטים של יניב ליבוביץ?',
            'type': 'person',
            'entity': 'יניב ליבוביץ',
            'description': 'Summarize projects by person'
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        print("="*80)
        print(f"TEST {i}/{len(test_queries)}: {test['description']}")
        print("="*80)
        print(f"Query: {fix_hebrew_rtl(test['query'])}")
        print()
        
        # Get expected count from DB
        expected_count = count_requests_in_db(db_conn, test['type'], test['entity'])
        sample_ids = get_sample_ids(db_conn, test['type'], test['entity'], 5)
        
        print(f"Expected from DB: {expected_count} requests")
        if sample_ids:
            print(f"Sample IDs: {sample_ids[:5]}")
        print()
        
        # Run RAG query
        print("Running RAG query...")
        start_query = time.time()
        
        try:
            result = rag.query(test['query'], top_k=20)
            query_time = time.time() - start_query
            
            answer = result.get('answer', 'No answer')
            retrieved_count = len(result.get('requests', []))
            retrieved_ids = [str(r['requestid']) for r in result.get('requests', [])]
            
            # Check matching
            matching_ids = [rid for rid in retrieved_ids if rid in sample_ids] if sample_ids else []
            
            print(f"✅ Query completed in {query_time:.2f} seconds")
            print()
            print("RAG Answer:")
            print(fix_hebrew_rtl(answer))
            print()
            print(f"Retrieved: {retrieved_count} requests")
            print(f"Matching with DB sample: {len(matching_ids)}/{len(sample_ids)}")
            if matching_ids:
                print(f"  Matching IDs: {matching_ids}")
            print()
            
            # Extract count from answer (if it's a count query)
            extracted_count = None
            if 'כמה' in test['query'] or 'count' in test['description'].lower():
                # Try to extract number from answer
                import re
                numbers = re.findall(r'\d+', answer)
                if numbers:
                    try:
                        extracted_count = int(numbers[0])
                    except:
                        pass
            
            # Assess accuracy
            accuracy = "✅ CORRECT" if extracted_count == expected_count else "⚠️ DIFFERENT"
            if extracted_count is None:
                accuracy = "❓ UNKNOWN"
            
            results.append({
                'test_num': i,
                'query': test['query'],
                'description': test['description'],
                'expected_count': expected_count,
                'extracted_count': extracted_count,
                'retrieved_count': retrieved_count,
                'matching_ids': len(matching_ids),
                'sample_ids': len(sample_ids),
                'query_time': query_time,
                'answer': answer,
                'accuracy': accuracy
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'test_num': i,
                'query': test['query'],
                'description': test['description'],
                'error': str(e)
            })
        
        print()
    
    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print()
    
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"Total tests: {len(test_queries)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print()
    
    if successful:
        avg_time = sum(r['query_time'] for r in successful) / len(successful)
        print(f"Average query time: {avg_time:.2f} seconds")
        print()
        
        print("Accuracy:")
        for r in successful:
            if 'extracted_count' in r and r['extracted_count'] is not None:
                print(f"  Test {r['test_num']}: Expected {r['expected_count']}, Got {r['extracted_count']} - {r['accuracy']}")
            else:
                print(f"  Test {r['test_num']}: {r['accuracy']} (couldn't extract count)")
        print()
        
        print("Retrieval matching:")
        for r in successful:
            print(f"  Test {r['test_num']}: {r['matching_ids']}/{r['sample_ids']} IDs matched")
    
    if failed:
        print("Failed tests:")
        for r in failed:
            print(f"  Test {r['test_num']}: {r['error']}")
    
    # Cleanup
    rag.close()
    db_conn.close()
    
    return results

if __name__ == '__main__':
    main()

