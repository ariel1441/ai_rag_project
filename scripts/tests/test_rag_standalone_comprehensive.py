"""
STANDALONE Comprehensive RAG Test - Run in separate terminal to avoid Cursor timeouts
This is the same as test_rag_full_comprehensive.py but designed for standalone execution.
"""
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
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

def count_requests_in_db(conn, query_type: str, entity) -> Optional[int]:
    """Count requests in database for verification."""
    cursor = conn.cursor()
    
    try:
        if query_type == 'person':
            cursor.execute("""
                SELECT COUNT(DISTINCT requestid)
                FROM requests
                WHERE updatedby ILIKE %s OR createdby ILIKE %s
            """, (f'%{entity}%', f'%{entity}%'))
        elif query_type == 'type':
            cursor.execute("""
                SELECT COUNT(DISTINCT requestid)
                FROM requests
                WHERE requesttypeid = %s
            """, (int(entity),))
        elif query_type == 'status':
            cursor.execute("""
                SELECT COUNT(DISTINCT requestid)
                FROM requests
                WHERE requeststatusid = %s
            """, (int(entity),))
        elif query_type == 'project':
            cursor.execute("""
                SELECT COUNT(DISTINCT requestid)
                FROM requests
                WHERE projectname ILIKE %s
            """, (f'%{entity}%',))
        else:
            return None
        
        count = cursor.fetchone()[0]
        return count
    finally:
        cursor.close()

def get_sample_ids(conn, query_type: str, entity, limit: int = 10) -> List[str]:
    """Get sample request IDs from database."""
    cursor = conn.cursor()
    
    try:
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
        elif query_type == 'project':
            cursor.execute("""
                SELECT DISTINCT requestid
                FROM requests
                WHERE projectname ILIKE %s
                ORDER BY requestid
                LIMIT %s
            """, (f'%{entity}%', limit))
        else:
            return []
        
        ids = [str(row[0]) for row in cursor.fetchall()]
        return ids
    finally:
        cursor.close()

def extract_count_from_answer(answer: str) -> Optional[int]:
    """Extract count number from answer text."""
    numbers = re.findall(r'\d+', answer)
    if numbers:
        try:
            return int(numbers[0])
        except:
            pass
    return None

def main():
    print("="*80)
    print("COMPREHENSIVE RAG TEST - STANDALONE VERSION")
    print("Run this in a separate terminal to avoid Cursor timeouts")
    print("="*80)
    print()
    
    # Track timing
    timing = {
        'init': 0,
        'first_model_load': 0,
        'subsequent_queries': []
    }
    
    # Connect to database
    print("Step 1: Connecting to database...")
    start_db = time.time()
    try:
        db_conn = get_db_connection()
        db_time = time.time() - start_db
        print(f"✅ Database connected in {db_time:.2f} seconds")
        print()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please ensure PostgreSQL is running on port 5433")
        return
    
    # Initialize RAG system
    print("Step 2: Initializing RAG system...")
    start_init = time.time()
    rag = RAGSystem()
    rag.connect_db()
    init_time = time.time() - start_init
    timing['init'] = init_time
    print(f"✅ RAG system initialized in {init_time:.2f} seconds")
    print()
    
    # Pre-load model (FIRST TIME - this is the slow part)
    print("Step 3: Pre-loading LLM model (FIRST TIME)...")
    print("⚠️  This is the FIRST TIME loading - will be slow (30-60 seconds)")
    print("    After this, subsequent queries will be fast (5-15 seconds)")
    print()
    print("⏳ IMPORTANT: Model loading is in progress...")
    print("   - This takes 30-60 seconds (loading ~4GB model from disk)")
    print("   - You'll see 'Loading checkpoint shards...' messages")
    print("   - Please DO NOT stop the process - it's working!")
    print("   - The process may appear 'stuck' but it's loading in the background")
    print()
    print("Starting model load now...")
    print("-" * 80)
    sys.stdout.flush()  # Force output to appear immediately
    
    start_model_load = time.time()
    try:
        rag.load_model()  # Load model upfront
        model_load_time = time.time() - start_model_load
        timing['first_model_load'] = model_load_time
        print("-" * 80)
        print(f"✅ Model loaded successfully in {model_load_time:.2f} seconds")
        print("✅ This was the FIRST TIME load - subsequent queries will be faster")
        print()
    except Exception as e:
        print("-" * 80)
        print(f"❌ Model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test queries - different types
    test_queries = [
        {
            'query': 'כמה פניות יש מאור גלילי?',
            'type': 'person',
            'entity': 'אור גלילי',
            'description': 'Count requests by person name (מא pattern)',
            'query_type': 'count'
        },
        {
            'query': 'כמה פניות יש מיניב ליבוביץ?',
            'type': 'person',
            'entity': 'יניב ליבוביץ',
            'description': 'Count requests by person name (מי pattern)',
            'query_type': 'count'
        },
        {
            'query': 'כמה פניות יש מאוקסנה כלפון?',
            'type': 'person',
            'entity': 'אוקסנה כלפון',
            'description': 'Count requests by person name (another person)',
            'query_type': 'count'
        },
        {
            'query': 'כמה בקשות יש מסוג 1?',
            'type': 'type',
            'entity': 1,
            'description': 'Count requests by type ID',
            'query_type': 'count'
        },
        {
            'query': 'כמה בקשות יש מסוג 2?',
            'type': 'type',
            'entity': 2,
            'description': 'Count requests by type ID (type 2)',
            'query_type': 'count'
        },
        {
            'query': 'תביא לי פניות מאור גלילי',
            'type': 'person',
            'entity': 'אור גלילי',
            'description': 'Find requests by person name',
            'query_type': 'find'
        },
        {
            'query': 'מה הפרויקטים של יניב ליבוביץ?',
            'type': 'person',
            'entity': 'יניב ליבוביץ',
            'description': 'Summarize projects by person',
            'query_type': 'summarize'
        },
        {
            'query': 'תסכם לי את כל הפניות מסוג 1',
            'type': 'type',
            'entity': 1,
            'description': 'Summarize requests by type',
            'query_type': 'summarize'
        }
    ]
    
    results = []
    
    print("="*80)
    print("Step 4: Running Test Queries")
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
        
        # Run RAG query
        print("Running RAG query...")
        start_query = time.time()
        
        try:
            result = rag.query(test['query'], top_k=20)
            query_time = time.time() - start_query
            timing['subsequent_queries'].append(query_time)
            
            answer = result.get('answer', 'No answer')
            retrieved_count = len(result.get('requests', []))
            retrieved_ids = [str(r['requestid']) for r in result.get('requests', [])]
            
            # Check matching
            matching_ids = [rid for rid in retrieved_ids if rid in sample_ids] if sample_ids else []
            
            print(f"✅ Query completed in {query_time:.2f} seconds")
            print()
            print("RAG Answer:")
            print("-" * 80)
            print(fix_hebrew_rtl(answer))
            print("-" * 80)
            print()
            print(f"Retrieved: {retrieved_count} requests")
            print(f"Matching with DB sample: {len(matching_ids)}/{min(len(sample_ids), 10)}")
            if matching_ids:
                print(f"  Matching IDs: {matching_ids[:5]}")
            print()
            
            # Extract count from answer (if it's a count query)
            extracted_count = None
            if test['query_type'] == 'count':
                extracted_count = extract_count_from_answer(answer)
            
            # Assess accuracy
            if test['query_type'] == 'count' and extracted_count is not None:
                if extracted_count == expected_count:
                    accuracy = "✅ CORRECT"
                elif abs(extracted_count - expected_count) <= 2:
                    accuracy = "⚠️ CLOSE (within 2)"
                else:
                    accuracy = f"❌ DIFFERENT (expected {expected_count}, got {extracted_count})"
            elif test['query_type'] == 'count':
                accuracy = "❓ UNKNOWN (couldn't extract count)"
            else:
                accuracy = "✅ ANSWER PROVIDED"
            
            results.append({
                'test_num': i,
                'query': test['query'],
                'description': test['description'],
                'query_type': test['query_type'],
                'expected_count': expected_count,
                'extracted_count': extracted_count,
                'retrieved_count': retrieved_count,
                'matching_ids': len(matching_ids),
                'sample_ids': len(sample_ids),
                'query_time': query_time,
                'answer': answer,
                'accuracy': accuracy,
                'retrieved_ids': retrieved_ids[:10]
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
    print("TEST SUMMARY")
    print("="*80)
    print()
    
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"Total tests: {len(test_queries)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed/Crashed: {len(failed)}")
    print()
    
    # Timing analysis
    print("="*80)
    print("SPEED ANALYSIS")
    print("="*80)
    print()
    print(f"Initialization time: {timing['init']:.2f} seconds")
    print(f"First model load time: {timing['first_model_load']:.2f} seconds")
    print(f"  ⚠️  This is the FIRST TIME load - slow but only happens once per session")
    print()
    
    if timing['subsequent_queries']:
        avg_query_time = sum(timing['subsequent_queries']) / len(timing['subsequent_queries'])
        min_query_time = min(timing['subsequent_queries'])
        max_query_time = max(timing['subsequent_queries'])
        
        print(f"Subsequent query times (after model loaded):")
        print(f"  Average: {avg_query_time:.2f} seconds")
        print(f"  Min: {min_query_time:.2f} seconds")
        print(f"  Max: {max_query_time:.2f} seconds")
        print(f"  ✅ These are FAST - model is already loaded in memory")
        print()
        print("ANSWER: First time slow = FIRST TIME PER SESSION (when model loads)")
        print("        After that, all queries are fast (5-15 seconds)")
        print()
    
    # Accuracy analysis
    print("="*80)
    print("ACCURACY ANALYSIS")
    print("="*80)
    print()
    
    count_tests = [r for r in successful if r.get('query_type') == 'count']
    if count_tests:
        print("Count Query Accuracy:")
        for r in count_tests:
            if r.get('extracted_count') is not None:
                print(f"  Test {r['test_num']}: {r['accuracy']}")
                print(f"    Expected: {r['expected_count']}, Got: {r['extracted_count']}")
            else:
                print(f"  Test {r['test_num']}: {r['accuracy']}")
        print()
    
    print("Retrieval Matching (how many retrieved IDs match DB sample):")
    for r in successful:
        print(f"  Test {r['test_num']}: {r['matching_ids']}/{min(r['sample_ids'], 10)} IDs matched")
    print()
    
    # Cleanup
    rag.close()
    db_conn.close()
    
    # Save results
    import json
    test_results = {
        'timing': timing,
        'results': results,
        'successful': len(successful),
        'failed': len(failed),
        'total': len(test_queries)
    }
    
    with open('test_results_data.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)
    
    print("="*80)
    print("Test results saved to test_results_data.json")
    print("="*80)
    
    return test_results

if __name__ == '__main__':
    main()

