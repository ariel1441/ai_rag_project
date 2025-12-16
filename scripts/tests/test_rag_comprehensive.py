"""
Comprehensive RAG Testing Script

Tests the RAG system with various example queries and compares results with CSV data.
"""
import sys
import os
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.rag_query import RAGSystem
from scripts.utils.hebrew import fix_hebrew_rtl

def load_csv_data():
    """Load request data from CSV for comparison."""
    csv_path = Path(__file__).parent.parent.parent / "data" / "raw" / "request.csv"
    if not csv_path.exists():
        print(f"⚠️  CSV file not found at {csv_path}")
        return None
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"✓ Loaded {len(df)} requests from CSV")
        return df
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return None

def verify_count_query(rag, query, csv_df, field_name, expected_value):
    """Verify count queries by comparing with CSV data."""
    print("\n" + "="*80)
    print(f"TEST: {query}")
    print("="*80)
    
    # Get actual count from CSV
    if field_name == 'UpdatedBy':
        actual_count = len(csv_df[csv_df['UpdatedBy'].str.contains(expected_value, na=False, case=False)])
    elif field_name == 'CreatedBy':
        actual_count = len(csv_df[csv_df['CreatedBy'].str.contains(expected_value, na=False, case=False)])
    elif field_name == 'RequestTypeId':
        actual_count = len(csv_df[csv_df['RequestTypeId'] == int(expected_value)])
    else:
        actual_count = None
    
    print(f"Expected count (from CSV): {actual_count}")
    print()
    
    # Run RAG query
    try:
        result = rag.query(query, top_k=20)
        
        print("\n" + "-"*80)
        print("RAG ANSWER:")
        print("-"*80)
        print(fix_hebrew_rtl(result['answer']))
        print()
        
        print("-"*80)
        print(f"RETRIEVED REQUESTS: {len(result['requests'])}")
        print("-"*80)
        for i, req in enumerate(result['requests'][:5], 1):
            print(f"{i}. Request {req['requestid']} - {req.get('projectname', 'N/A')}")
            if req.get('updatedby'):
                print(f"   Updated By: {fix_hebrew_rtl(str(req['updatedby']))}")
            if req.get('createdby'):
                print(f"   Created By: {fix_hebrew_rtl(str(req['createdby']))}")
            print(f"   Similarity: {req.get('similarity', 0):.4f}")
            print()
        
        # Check if answer contains the count
        answer_lower = result['answer'].lower()
        if actual_count and str(actual_count) in answer_lower:
            print(f"✅ Answer contains expected count: {actual_count}")
        elif actual_count:
            print(f"⚠️  Answer doesn't contain expected count {actual_count}")
            print(f"   Answer: {result['answer'][:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_rag_system():
    """Run comprehensive tests on RAG system."""
    print("="*80)
    print("COMPREHENSIVE RAG SYSTEM TESTING")
    print("="*80)
    print()
    
    # Load CSV data for comparison
    csv_df = load_csv_data()
    if csv_df is None:
        print("⚠️  Continuing without CSV comparison...")
    
    # Initialize RAG system
    print("Initializing RAG system...")
    rag = RAGSystem()
    
    try:
        # Connect to database
        print("Connecting to database...")
        rag.connect_db()
        print("✓ Database connected")
        print()
        
        # Load model (will be done on first query if not loaded)
        print("Note: Model will be loaded on first query (takes 30-60 seconds)")
        print()
        
        # Test queries based on examples from documentation
        test_queries = [
            # Count queries
            {
                'query': 'כמה פניות יש מיניב ליבוביץ?',
                'type': 'count',
                'field': 'UpdatedBy',
                'value': 'יניב ליבוביץ',
                'description': 'Count requests from יניב ליבוביץ'
            },
            {
                'query': 'כמה פניות יש מאוקסנה כלפון?',
                'type': 'count',
                'field': 'UpdatedBy',
                'value': 'אוקסנה כלפון',
                'description': 'Count requests from אוקסנה כלפון'
            },
            {
                'query': 'כמה בקשות יש מסוג 4?',
                'type': 'count',
                'field': 'RequestTypeId',
                'value': '4',
                'description': 'Count requests of type 4'
            },
            # Find queries
            {
                'query': 'תביא לי פניות מיניב ליבוביץ',
                'type': 'find',
                'field': 'UpdatedBy',
                'value': 'יניב ליבוביץ',
                'description': 'Find requests from יניב ליבוביץ'
            },
            {
                'query': 'תביא לי פניות מסוג 1',
                'type': 'find',
                'field': 'RequestTypeId',
                'value': '1',
                'description': 'Find requests of type 1'
            },
            # Summarize queries
            {
                'query': 'תביא לי סיכום של כל הפניות מסוג 2',
                'type': 'summarize',
                'field': 'RequestTypeId',
                'value': '2',
                'description': 'Summarize requests of type 2'
            },
        ]
        
        results = []
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{'='*80}")
            print(f"TEST {i}/{len(test_queries)}: {test_case['description']}")
            print(f"{'='*80}")
            
            if csv_df is not None:
                result = verify_count_query(
                    rag, 
                    test_case['query'],
                    csv_df,
                    test_case['field'],
                    test_case['value']
                )
            else:
                # Just run the query without CSV comparison
                print(f"Query: {fix_hebrew_rtl(test_case['query'])}")
                print()
                try:
                    result = rag.query(test_case['query'], top_k=20)
                    print("\n" + "-"*80)
                    print("RAG ANSWER:")
                    print("-"*80)
                    print(fix_hebrew_rtl(result['answer']))
                    print()
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    result = None
            
            results.append({
                'test_case': test_case,
                'result': result
            })
            
            # Small delay between queries
            import time
            time.sleep(1)
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        successful = sum(1 for r in results if r['result'] is not None)
        print(f"Successful tests: {successful}/{len(test_queries)}")
        
        for i, r in enumerate(results, 1):
            status = "✅" if r['result'] is not None else "❌"
            print(f"{status} Test {i}: {r['test_case']['description']}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rag.close()
        print("\n✓ RAG system closed")

if __name__ == "__main__":
    test_rag_system()

