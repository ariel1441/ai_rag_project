"""
Test RAG Retrieval Only (No LLM) - Fast Test
This tests the retrieval part without loading the LLM model.
Use this to verify search/retrieval works before testing full RAG.
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

def count_requests_in_db(conn, query_type: str, entity):
    """Count requests in database for verification.
    
    For person queries, checks multiple fields where the name might appear:
    - updatedby, createdby (most common)
    - projectname (also common)
    - responsibleemployeename (sometimes)
    """
    cursor = conn.cursor()
    
    try:
        if query_type == 'person':
            # Check multiple fields where person name might appear
            cursor.execute("""
                SELECT COUNT(DISTINCT requestid)
                FROM requests
                WHERE updatedby ILIKE %s 
                   OR createdby ILIKE %s
                   OR projectname ILIKE %s
                   OR responsibleemployeename ILIKE %s
            """, (f'%{entity}%', f'%{entity}%', f'%{entity}%', f'%{entity}%'))
        elif query_type == 'type':
            cursor.execute("""
                SELECT COUNT(DISTINCT requestid)
                FROM requests
                WHERE requesttypeid::text = %s
            """, (str(entity),))
        else:
            return None
        
        count = cursor.fetchone()[0]
        return count
    finally:
        cursor.close()

def get_sample_ids(conn, query_type: str, entity, limit: int = 10):
    """Get sample request IDs from database."""
    cursor = conn.cursor()
    
    try:
        if query_type == 'person':
            # Check multiple fields where person name might appear
            cursor.execute("""
                SELECT DISTINCT requestid
                FROM requests
                WHERE updatedby ILIKE %s 
                   OR createdby ILIKE %s
                   OR projectname ILIKE %s
                   OR responsibleemployeename ILIKE %s
                ORDER BY requestid
                LIMIT %s
            """, (f'%{entity}%', f'%{entity}%', f'%{entity}%', f'%{entity}%', limit))
        elif query_type == 'type':
            cursor.execute("""
                SELECT DISTINCT requestid
                FROM requests
                WHERE requesttypeid::text = %s
                ORDER BY requestid
                LIMIT %s
            """, (str(entity), limit))
        else:
            return []
        
        ids = [str(row[0]) for row in cursor.fetchall()]
        return ids
    finally:
        cursor.close()

def main():
    print("="*80)
    print("RAG RETRIEVAL TEST (NO LLM - FAST)")
    print("This tests retrieval/search without loading the LLM model")
    print("="*80)
    print()
    
    # Connect to database
    print("Step 1: Connecting to database...")
    start_db = time.time()
    db_conn = get_db_connection()
    db_time = time.time() - start_db
    print(f"✅ Database connected in {db_time:.2f} seconds")
    print()
    
    # Initialize RAG system (but DON'T load LLM model)
    print("Step 2: Initializing RAG system (NO LLM loading)...")
    start_init = time.time()
    rag = RAGSystem()
    rag.connect_db()
    init_time = time.time() - start_init
    print(f"✅ RAG system initialized in {init_time:.2f} seconds")
    print("⚠️  LLM model NOT loaded - only testing retrieval/search")
    print()
    
    # Test queries - just retrieval
    test_queries = [
        {
            'query': 'כמה פניות יש מאור גלילי?',
            'type': 'person',
            'entity': 'אור גלילי',
            'description': 'Retrieve requests by person name (מא pattern)'
        },
        {
            'query': 'כמה פניות יש מיניב ליבוביץ?',
            'type': 'person',
            'entity': 'יניב ליבוביץ',
            'description': 'Retrieve requests by person name (מי pattern)'
        },
        {
            'query': 'כמה פניות יש מאוקסנה כלפון?',
            'type': 'person',
            'entity': 'אוקסנה כלפון',
            'description': 'Retrieve requests by person name (another person)'
        },
        {
            'query': 'כמה בקשות יש מסוג 1?',
            'type': 'type',
            'entity': 1,
            'description': 'Retrieve requests by type ID'
        },
        {
            'query': 'תביא לי פניות מאור גלילי',
            'type': 'person',
            'entity': 'אור גלילי',
            'description': 'Find requests by person name'
        }
    ]
    
    results = []
    
    print("="*80)
    print("Step 3: Testing Retrieval (Search Only)")
    print("="*80)
    print()
    
    for i, test in enumerate(test_queries, 1):
        print("="*80)
        print(f"TEST {i}/{len(test_queries)}: {test['description']}")
        print("="*80)
        print(f"Query: {fix_hebrew_rtl(test['query'])}")
        print()
        
        # Get expected count from DB
        expected_count = count_requests_in_db(db_conn, test['type'], test['entity'])
        sample_ids = get_sample_ids(db_conn, test['type'], test['entity'], 10)
        
        print(f"Expected from DB: {expected_count} requests")
        if sample_ids:
            print(f"Sample IDs from DB: {sample_ids[:5]}...")
        print()
        
        # Test retrieval only (no LLM generation)
        print("Testing retrieval (search only, no LLM)...")
        start_query = time.time()
        
        try:
            # Use retrieve_requests directly (no LLM needed)
            retrieved = rag.retrieve_requests(test['query'], top_k=20)
            query_time = time.time() - start_query
            
            retrieved_count = len(retrieved)
            retrieved_ids = [str(r['requestid']) for r in retrieved]
            
            # Check matching
            matching_ids = [rid for rid in retrieved_ids if rid in sample_ids] if sample_ids else []
            
            print(f"✅ Retrieval completed in {query_time:.2f} seconds")
            print()
            print(f"Retrieved: {retrieved_count} requests")
            print(f"Matching with DB sample: {len(matching_ids)}/{min(len(sample_ids), 10)}")
            if matching_ids:
                print(f"  Matching IDs: {matching_ids[:5]}")
            print()
            
            # Show top 3 retrieved requests
            print("Top 3 retrieved requests:")
            for j, req in enumerate(retrieved[:3], 1):
                print(f"  {j}. Request ID: {req['requestid']}")
                if req.get('projectname'):
                    print(f"     Project: {req['projectname']}")
                if req.get('updatedby'):
                    print(f"     Updated By: {req['updatedby']}")
                if req.get('similarity'):
                    print(f"     Similarity: {req['similarity']:.3f}")
            print()
            
            results.append({
                'test_num': i,
                'query': test['query'],
                'description': test['description'],
                'expected_count': expected_count,
                'retrieved_count': retrieved_count,
                'matching_ids': len(matching_ids),
                'sample_ids': len(sample_ids),
                'query_time': query_time,
                'accuracy': "✅ GOOD" if len(matching_ids) > 0 else "⚠️ NO MATCHES"
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'test_num': i,
                'query': test['query'],
                'description': test['description'],
                'error': str(e),
                'crashed': True
            })
        
        print()
    
    # Summary
    print("="*80)
    print("RETRIEVAL TEST SUMMARY")
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
        print(f"Average retrieval time: {avg_time:.2f} seconds")
        print("✅ Retrieval is FAST (no LLM loading needed)")
        print()
        
        print("Retrieval Accuracy:")
        for r in successful:
            print(f"  Test {r['test_num']}: {r['accuracy']} - {r['matching_ids']}/{min(r['sample_ids'], 10)} IDs matched")
        print()
    
    if failed:
        print("Failed tests:")
        for r in failed:
            print(f"  Test {r['test_num']}: {r['error']}")
    
    # Cleanup
    rag.close()
    db_conn.close()
    
    print("="*80)
    print("✅ Retrieval test complete!")
    print("   If retrieval works, then the issue is with LLM model loading")
    print("   Next step: Test LLM loading separately")
    print("="*80)
    
    return results

if __name__ == '__main__':
    main()
