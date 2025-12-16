"""
Simple RAG Test - Standalone (can run in separate terminal)
This version handles model loading better and provides progress updates.
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("="*80)
print("SIMPLE RAG TEST - STANDALONE")
print("="*80)
print()
print("This test will:")
print("  1. Load the model (30-60 seconds - be patient!)")
print("  2. Run a few test queries")
print("  3. Compare results with database")
print()
print("Note: If you see 'Loading checkpoint shards', this is normal.")
print("      It may take 1-2 minutes to load all 3 shards.")
print()

try:
    from scripts.core.rag_query import RAGSystem
    from scripts.utils.hebrew import fix_hebrew_rtl
    import psycopg2
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Connect to database
    print("Step 1: Connecting to database...")
    db_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5433')),
        database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    print("✅ Database connected")
    print()
    
    # Initialize RAG
    print("Step 2: Initializing RAG system...")
    rag = RAGSystem()
    rag.connect_db()
    print("✅ RAG system initialized")
    print()
    
    # Load model (this is the slow part)
    print("Step 3: Loading LLM model...")
    print("⚠️  This will take 30-60 seconds (or 1-2 minutes on first load)")
    print("    Loading checkpoint shards: 0% → 33% → 66% → 100%")
    print("    Please be patient - this only happens once!")
    print()
    
    start_load = time.time()
    try:
        rag.load_model()
        load_time = time.time() - start_load
        print(f"✅ Model loaded successfully in {load_time:.2f} seconds")
        print()
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("This might be a timeout issue. Try running in a separate terminal.")
        raise
    
    # Test queries
    test_queries = [
        {
            'query': 'כמה פניות יש מאור גלילי?',
            'description': 'Count requests by person name'
        },
        {
            'query': 'כמה בקשות יש מסוג 1?',
            'description': 'Count requests by type'
        }
    ]
    
    print("Step 4: Running test queries...")
    print()
    
    for i, test in enumerate(test_queries, 1):
        print(f"Test {i}: {test['description']}")
        print(f"Query: {fix_hebrew_rtl(test['query'])}")
        print()
        
        start_query = time.time()
        try:
            result = rag.query(test['query'], top_k=20)
            query_time = time.time() - start_query
            
            answer = result.get('answer', 'No answer')
            retrieved_count = len(result.get('requests', []))
            
            print(f"✅ Query completed in {query_time:.2f} seconds")
            print()
            print("Answer:")
            print(fix_hebrew_rtl(answer))
            print()
            print(f"Retrieved: {retrieved_count} requests")
            print()
            print("-"*80)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # Cleanup
    rag.close()
    db_conn.close()
    
    print("="*80)
    print("TEST COMPLETE")
    print("="*80)
    
except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
except Exception as e:
    print(f"\n\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

