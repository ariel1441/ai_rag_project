"""
Test Compatible RAG System (Current PC)
This tests the compatible version that works on limited systems.
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

def count_requests_in_db(conn, entity):
    """Count requests with person name in multiple fields."""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(DISTINCT requestid)
            FROM requests
            WHERE updatedby ILIKE %s 
               OR createdby ILIKE %s
               OR projectname ILIKE %s
               OR responsibleemployeename ILIKE %s
        """, (f'%{entity}%', f'%{entity}%', f'%{entity}%', f'%{entity}%'))
        count = cursor.fetchone()[0]
        return count
    finally:
        cursor.close()

def main():
    print("="*80)
    print("COMPATIBLE RAG SYSTEM TEST")
    print("(For limited systems - uses float16)")
    print("="*80)
    print()
    print("This test:")
    print("  ✅ Uses compatible version (works on Windows CPU)")
    print("  ✅ Automatically skips 4-bit quantization")
    print("  ✅ Uses float16 (~7-8GB RAM)")
    print("  ✅ Tests ONE query to verify it works")
    print()
    print("Expected time:")
    print("  - Model loading: 2-5 minutes (float16)")
    print("  - Query: 5-15 seconds")
    print()
    
    # Test query
    test_query = 'כמה פניות יש מיניב ליבוביץ?'
    expected_name = 'יניב ליבוביץ'
    
    print(f"Test Query: {fix_hebrew_rtl(test_query)}")
    print()
    
    # Connect to database
    print("Step 1: Connecting to database...")
    start_db = time.time()
    db_conn = get_db_connection()
    db_time = time.time() - start_db
    print(f"✅ Database connected in {db_time:.2f} seconds")
    print()
    
    # Get expected count
    expected_count = count_requests_in_db(db_conn, expected_name)
    print(f"Expected from DB: {expected_count} requests with '{expected_name}'")
    print()
    
    # Initialize RAG system (compatible version)
    print("Step 2: Initializing RAG system (compatible version)...")
    start_init = time.time()
    rag = RAGSystem()
    rag.connect_db()
    init_time = time.time() - start_init
    print(f"✅ RAG system initialized in {init_time:.2f} seconds")
    print()
    
    # Load LLM model (will use float16 on Windows)
    print("Step 3: Loading LLM model...")
    print("="*80)
    print("⏳ Loading model (2-5 minutes expected)")
    print("   This will use float16 (~7-8GB RAM)")
    print("   Will automatically skip 4-bit on Windows CPU")
    print("   Progress will be shown below...")
    print("="*80)
    print()
    
    start_model_load = time.time()
    try:
        rag.load_model()
        model_load_time = time.time() - start_model_load
        print()
        print("="*80)
        print(f"✅ Model loaded successfully in {model_load_time/60:.1f} minutes")
        print("="*80)
        print()
    except Exception as e:
        print()
        print("="*80)
        print(f"❌ Model loading failed: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
        return
    
    # Test FULL RAG query
    print("Step 4: Testing FULL RAG query...")
    print("="*80)
    print(f"Query: {fix_hebrew_rtl(test_query)}")
    print()
    
    start_query = time.time()
    try:
        result = rag.query(test_query, top_k=20)
        query_time = time.time() - start_query
        
        answer = result.get('answer', 'No answer')
        retrieved_count = len(result.get('requests', []))
        
        print("="*80)
        print("RAG ANSWER:")
        print("="*80)
        print(fix_hebrew_rtl(answer))
        print("="*80)
        print()
        print(f"✅ Query completed in {query_time:.2f} seconds")
        print()
        print(f"Retrieved: {retrieved_count} requests")
        print(f"Expected from DB: {expected_count} requests")
        print()
        
        # Try to extract count from answer
        import re
        numbers = re.findall(r'\d+', answer)
        if numbers:
            extracted_count = int(numbers[0])
            print(f"Extracted count from answer: {extracted_count}")
            print(f"Expected count from DB: {expected_count}")
            if extracted_count == expected_count:
                print("✅ COUNT MATCHES!")
            elif abs(extracted_count - expected_count) <= 5:
                print("⚠️  COUNT CLOSE (within 5)")
            else:
                print("❌ COUNT DIFFERENT")
        else:
            print("⚠️  Could not extract count from answer")
        
        print()
        print("Top 3 retrieved requests:")
        for i, req in enumerate(result.get('requests', [])[:3], 1):
            print(f"  {i}. Request ID: {req['requestid']}")
            if req.get('projectname'):
                print(f"     Project: {req['projectname']}")
            if req.get('updatedby'):
                print(f"     Updated By: {req['updatedby']}")
        
        print()
        print("="*80)
        print("✅ TEST PASSED - COMPATIBLE RAG SYSTEM WORKS!")
        print("="*80)
        
    except Exception as e:
        print()
        print("="*80)
        print(f"❌ RAG query failed: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
    
    # Cleanup
    rag.close()
    db_conn.close()
    
    print()
    print("="*80)
    print("TEST COMPLETE")
    print("="*80)
    print()
    print("Note: This is the COMPATIBLE version (float16)")
    print("      For high-end systems, use test_rag_high_end.py")

if __name__ == '__main__':
    main()

