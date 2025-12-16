"""
Automated RAG Testing - No user input required
Runs multiple test queries and compares with CSV data
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
        return None
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def get_actual_count(csv_df, field_name, value):
    """Get actual count from CSV."""
    if csv_df is None:
        return None
    
    try:
        if field_name == 'UpdatedBy':
            # Case-insensitive partial match
            mask = csv_df['UpdatedBy'].astype(str).str.contains(str(value), na=False, case=False, regex=False)
            return mask.sum()
        elif field_name == 'CreatedBy':
            mask = csv_df['CreatedBy'].astype(str).str.contains(str(value), na=False, case=False, regex=False)
            return mask.sum()
        elif field_name == 'RequestTypeId':
            mask = csv_df['RequestTypeId'] == int(value)
            return mask.sum()
        elif field_name == 'RequestStatusId':
            mask = csv_df['RequestStatusId'] == int(value)
            return mask.sum()
    except Exception as e:
        print(f"Error counting in CSV: {e}")
        return None
    
    return None

def test_query(rag, query, csv_df, field_name=None, expected_value=None, description=""):
    """Test a single query and return results."""
    print("\n" + "="*80)
    print(f"TEST: {description}")
    print(f"Query: {fix_hebrew_rtl(query)}")
    print("="*80)
    
    result = {
        'query': query,
        'description': description,
        'success': False,
        'answer': None,
        'retrieved_count': 0,
        'expected_count': None,
        'actual_count': None,
        'requests': [],
        'error': None
    }
    
    # Get expected count from CSV
    if csv_df is not None and field_name and expected_value:
        result['expected_count'] = get_actual_count(csv_df, field_name, expected_value)
        print(f"Expected count (from CSV): {result['expected_count']}")
    
    try:
        # Run RAG query
        rag_result = rag.query(query, top_k=20)
        
        result['answer'] = rag_result['answer']
        result['retrieved_count'] = len(rag_result['requests'])
        result['requests'] = rag_result['requests'][:10]  # Top 10
        result['parsed'] = rag_result.get('parsed', {})
        result['success'] = True
        
        print(f"\n✓ Query successful")
        print(f"Retrieved {result['retrieved_count']} requests")
        print(f"\nAnswer:")
        print(fix_hebrew_rtl(result['answer']))
        
        # Check if answer contains expected count
        if result['expected_count'] is not None:
            answer_lower = result['answer'].lower()
            expected_str = str(result['expected_count'])
            if expected_str in answer_lower:
                print(f"\n✅ Answer contains expected count: {result['expected_count']}")
            else:
                print(f"\n⚠️  Answer doesn't contain expected count {result['expected_count']}")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def run_all_tests():
    """Run all automated tests."""
    print("="*80)
    print("AUTOMATED RAG SYSTEM TESTING")
    print("="*80)
    print()
    
    # Load CSV data
    print("Loading CSV data for comparison...")
    csv_df = load_csv_data()
    if csv_df is not None:
        print(f"✓ Loaded {len(csv_df)} requests from CSV")
    else:
        print("⚠️  CSV not available, continuing without comparison")
    print()
    
    # Initialize RAG
    print("Initializing RAG system...")
    rag = RAGSystem()
    
    try:
        # Connect to database
        print("Connecting to database...")
        rag.connect_db()
        print("✓ Database connected")
        print()
        
        # Define test cases
        test_cases = [
            {
                'query': 'כמה פניות יש מיניב ליבוביץ?',
                'field': 'UpdatedBy',
                'value': 'יניב ליבוביץ',
                'description': 'Count requests from יניב ליבוביץ'
            },
            {
                'query': 'כמה פניות יש מאוקסנה כלפון?',
                'field': 'UpdatedBy',
                'value': 'אוקסנה כלפון',
                'description': 'Count requests from אוקסנה כלפון'
            },
            {
                'query': 'כמה בקשות יש מסוג 1?',
                'field': 'RequestTypeId',
                'value': '1',
                'description': 'Count requests of type 1'
            },
            {
                'query': 'כמה בקשות יש מסוג 2?',
                'field': 'RequestTypeId',
                'value': '2',
                'description': 'Count requests of type 2'
            },
            {
                'query': 'תביא לי פניות מיניב ליבוביץ',
                'field': 'UpdatedBy',
                'value': 'יניב ליבוביץ',
                'description': 'Find requests from יניב ליבוביץ'
            },
            {
                'query': 'תביא לי פניות מסוג 1',
                'field': 'RequestTypeId',
                'value': '1',
                'description': 'Find requests of type 1'
            },
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"TEST {i}/{len(test_cases)}")
            print(f"{'='*80}")
            
            result = test_query(
                rag,
                test_case['query'],
                csv_df,
                test_case.get('field'),
                test_case.get('value'),
                test_case['description']
            )
            
            results.append(result)
            
            # Small delay between queries
            import time
            time.sleep(1)
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        successful = sum(1 for r in results if r['success'])
        print(f"\nSuccessful tests: {successful}/{len(test_cases)}")
        
        for i, r in enumerate(results, 1):
            status = "✅" if r['success'] else "❌"
            print(f"\n{status} Test {i}: {r['description']}")
            if r['success']:
                print(f"   Retrieved: {r['retrieved_count']} requests")
                if r['expected_count'] is not None:
                    print(f"   Expected: {r['expected_count']} requests")
            else:
                print(f"   Error: {r['error']}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        rag.close()
        print("\n✓ RAG system closed")

if __name__ == "__main__":
    results = run_all_tests()
    
    # Print detailed results
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    
    for i, r in enumerate(results, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {r['description']}")
        print(f"{'='*80}")
        print(f"Query: {fix_hebrew_rtl(r['query'])}")
        print(f"Success: {r['success']}")
        if r['success']:
            print(f"\nAnswer:")
            print(fix_hebrew_rtl(r['answer']))
            print(f"\nRetrieved {r['retrieved_count']} requests")
            if r['expected_count'] is not None:
                print(f"Expected from CSV: {r['expected_count']}")
            print(f"\nTop 5 Retrieved Requests:")
            for j, req in enumerate(r['requests'][:5], 1):
                print(f"  {j}. Request {req['requestid']}")
                if req.get('projectname'):
                    print(f"     Project: {fix_hebrew_rtl(str(req['projectname']))}")
                if req.get('updatedby'):
                    print(f"     Updated By: {fix_hebrew_rtl(str(req['updatedby']))}")
                print(f"     Similarity: {req.get('similarity', 0):.4f}")
        else:
            print(f"Error: {r['error']}")

