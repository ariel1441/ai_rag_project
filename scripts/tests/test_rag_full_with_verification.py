"""
Full RAG Test with Verification
Tests RAG system and compares with CSV data, shows detailed results
"""
import sys
from pathlib import Path
import pandas as pd
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.rag_query import RAGSystem
from scripts.utils.hebrew import fix_hebrew_rtl

def load_csv_data():
    """Load CSV for comparison."""
    csv_path = Path(__file__).parent.parent.parent / "data" / "raw" / "request.csv"
    if not csv_path.exists():
        return None
    try:
        return pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
    except:
        return None

def get_csv_count(df, field, value):
    """Get count from CSV."""
    if df is None:
        return None
    try:
        if field == 'UpdatedBy':
            return df['UpdatedBy'].astype(str).str.contains(str(value), na=False, case=False, regex=False).sum()
        elif field == 'RequestTypeId':
            return (df['RequestTypeId'] == int(value)).sum()
    except:
        return None
    return None

def get_csv_sample(df, field, value, limit=5):
    """Get sample requests from CSV."""
    if df is None:
        return []
    try:
        if field == 'UpdatedBy':
            mask = df['UpdatedBy'].astype(str).str.contains(str(value), na=False, case=False, regex=False)
        elif field == 'RequestTypeId':
            mask = df['RequestTypeId'] == int(value)
        else:
            return []
        
        sample = df[mask].head(limit)
        results = []
        for _, row in sample.iterrows():
            results.append({
                'RequestId': str(row.get('RequestId', '')),
                'ProjectName': str(row.get('ProjectName', '')),
                'UpdatedBy': str(row.get('UpdatedBy', '')),
                'CreatedBy': str(row.get('CreatedBy', '')),
                'RequestTypeId': str(row.get('RequestTypeId', '')),
                'RequestStatusId': str(row.get('RequestStatusId', ''))
            })
        return results
    except:
        return []

def test_and_verify(rag, query, csv_df, field=None, value=None, description=""):
    """Test query and verify results."""
    print("\n" + "="*80)
    print(f"TEST: {description}")
    print("="*80)
    print(f"Query: {fix_hebrew_rtl(query)}")
    print()
    
    result = {
        'query': query,
        'description': description,
        'success': False,
        'answer': None,
        'retrieved_requests': [],
        'retrieved_count': 0,
        'expected_count': None,
        'csv_sample': [],
        'parsed': {},
        'error': None,
        'verification': {}
    }
    
    # Get expected from CSV
    if csv_df is not None and field and value:
        result['expected_count'] = get_csv_count(csv_df, field, value)
        result['csv_sample'] = get_csv_sample(csv_df, field, value, limit=10)
        print(f"Expected from CSV: {result['expected_count']} requests")
        print()
    
    try:
        # Run RAG
        rag_result = rag.query(query, top_k=20)
        
        result['success'] = True
        result['answer'] = rag_result['answer']
        result['retrieved_count'] = len(rag_result['requests'])
        result['retrieved_requests'] = rag_result['requests'][:10]
        result['parsed'] = rag_result.get('parsed', {})
        
        print(f"✓ RAG Query Successful")
        print(f"Retrieved: {result['retrieved_count']} requests")
        print()
        print("Answer:")
        print(fix_hebrew_rtl(result['answer']))
        print()
        
        # Verification
        if result['expected_count'] is not None:
            answer_lower = result['answer'].lower()
            expected_str = str(result['expected_count'])
            
            # Check if answer contains expected count
            contains_count = expected_str in answer_lower or any(word in answer_lower for word in [expected_str, f"{expected_str} פניות", f"{expected_str} בקשות"])
            
            result['verification'] = {
                'contains_expected_count': contains_count,
                'expected_count': result['expected_count'],
                'retrieved_count': result['retrieved_count'],
                'count_match': abs(result['retrieved_count'] - result['expected_count']) <= 5  # Allow small difference
            }
            
            if contains_count:
                print(f"✅ Answer contains expected count: {result['expected_count']}")
            else:
                print(f"⚠️  Answer doesn't clearly contain expected count {result['expected_count']}")
        
        # Check retrieved requests match CSV
        if result['csv_sample'] and result['retrieved_requests']:
            csv_ids = {str(r['RequestId']) for r in result['csv_sample']}
            retrieved_ids = {str(r['requestid']) for r in result['retrieved_requests']}
            matching = csv_ids.intersection(retrieved_ids)
            
            result['verification']['matching_ids'] = len(matching)
            result['verification']['csv_ids'] = list(csv_ids)
            result['verification']['retrieved_ids'] = list(retrieved_ids)[:10]
            
            print(f"\nRetrieved Request IDs: {list(retrieved_ids)[:10]}")
            print(f"CSV Sample IDs: {list(csv_ids)}")
            print(f"Matching: {len(matching)}/{len(csv_ids)}")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def main():
    """Run all tests."""
    print("="*80)
    print("FULL RAG SYSTEM TESTING WITH VERIFICATION")
    print("="*80)
    print()
    
    # Load CSV
    csv_df = load_csv_data()
    if csv_df is not None:
        print(f"✓ Loaded {len(csv_df)} requests from CSV for comparison")
    else:
        print("⚠️  CSV not available")
    print()
    
    # Initialize RAG
    rag = RAGSystem()
    
    try:
        rag.connect_db()
        print("✓ Database connected")
        print()
        
        # Test cases
        tests = [
            {
                'query': 'כמה פניות יש מיניב ליבוביץ?',
                'field': 'UpdatedBy',
                'value': 'יניב ליבוביץ',
                'description': 'Count: יניב ליבוביץ (Expected: 120)'
            },
            {
                'query': 'כמה פניות יש מאוקסנה כלפון?',
                'field': 'UpdatedBy',
                'value': 'אוקסנה כלפון',
                'description': 'Count: אוקסנה כלפון (Expected: 78)'
            },
            {
                'query': 'כמה בקשות יש מסוג 1?',
                'field': 'RequestTypeId',
                'value': '1',
                'description': 'Count: Type 1 (Expected: 2114)'
            },
            {
                'query': 'תביא לי פניות מיניב ליבוביץ',
                'field': 'UpdatedBy',
                'value': 'יניב ליבוביץ',
                'description': 'Find: יניב ליבוביץ'
            },
        ]
        
        results = []
        for i, test in enumerate(tests, 1):
            print(f"\n{'#'*80}")
            print(f"TEST {i}/{len(tests)}")
            print(f"{'#'*80}")
            result = test_and_verify(rag, test['query'], csv_df, test.get('field'), test.get('value'), test['description'])
            results.append(result)
            import time
            time.sleep(2)  # Delay between queries
        
        # Final Report
        print("\n" + "="*80)
        print("FINAL TEST REPORT")
        print("="*80)
        
        for i, r in enumerate(results, 1):
            print(f"\n{'='*80}")
            print(f"TEST {i}: {r['description']}")
            print(f"{'='*80}")
            print(f"Query: {fix_hebrew_rtl(r['query'])}")
            print(f"Status: {'✅ SUCCESS' if r['success'] else '❌ FAILED'}")
            
            if r['success']:
                print(f"\nRAG Answer:")
                print(fix_hebrew_rtl(r['answer']))
                print(f"\nRetrieved: {r['retrieved_count']} requests")
                
                if r['expected_count'] is not None:
                    print(f"Expected: {r['expected_count']} requests")
                    diff = abs(r['retrieved_count'] - r['expected_count'])
                    if diff <= 5:
                        print(f"✅ Count is close (difference: {diff})")
                    else:
                        print(f"⚠️  Count differs significantly (difference: {diff})")
                
                print(f"\nTop 5 Retrieved Requests:")
                for j, req in enumerate(r['retrieved_requests'][:5], 1):
                    print(f"  {j}. Request {req['requestid']}")
                    if req.get('projectname'):
                        print(f"     Project: {fix_hebrew_rtl(str(req['projectname']))}")
                    if req.get('updatedby'):
                        print(f"     Updated By: {fix_hebrew_rtl(str(req['updatedby']))}")
                    print(f"     Similarity: {req.get('similarity', 0):.4f}")
                
                if r['csv_sample']:
                    print(f"\nCSV Sample (for comparison):")
                    for j, req in enumerate(r['csv_sample'][:5], 1):
                        print(f"  {j}. Request {req['RequestId']}")
                        print(f"     Project: {fix_hebrew_rtl(req['ProjectName'])}")
                        print(f"     Updated By: {fix_hebrew_rtl(req['UpdatedBy'])}")
                
                # Check for hallucinations
                retrieved_ids = {str(req['requestid']) for req in r['retrieved_requests']}
                if r['csv_sample']:
                    csv_ids = {str(req['RequestId']) for req in r['csv_sample']}
                    not_in_csv = retrieved_ids - csv_ids
                    if not_in_csv:
                        print(f"\n⚠️  Some retrieved requests not in CSV sample: {list(not_in_csv)[:5]}")
                    else:
                        print(f"\n✅ All retrieved requests match CSV sample")
            else:
                print(f"Error: {r['error']}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        rag.close()

if __name__ == "__main__":
    results = main()

