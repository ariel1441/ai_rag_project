"""
Test AND logic implementation to verify it works correctly.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def test_and_logic():
    """Test AND logic with various queries."""
    print("=" * 80)
    print("TESTING AND LOGIC IMPLEMENTATION")
    print("=" * 80)
    print()
    
    search_service = SearchService()
    search_service.connect_db()
    
    test_cases = [
        {
            'name': 'Single entity - person',
            'query': 'פניות מאור גלילי',
            'expected': 'Should return results (not 0)',
        },
        {
            'name': 'Single entity - type',
            'query': 'בקשות מסוג 10',
            'expected': 'Should return results (not 0)',
        },
        {
            'name': 'Multiple entities - person + type',
            'query': 'בקשות מאור גלילי מסוג 10',
            'expected': 'Should return FEWER results than single person query',
        },
        {
            'name': 'Single entity - status',
            'query': 'בקשות בסטטוס 1',
            'expected': 'Should return results (not 0)',
        },
        {
            'name': 'Multiple entities - person + status',
            'query': 'פניות מיניב ליבוביץ בסטטוס 1',
            'expected': 'Should return results (not 0)',
        },
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        print(f"  Query: {test_case['query']}")
        
        try:
            search_results, count = search_service.search(test_case['query'], top_k=20)
            print(f"  Results: {count} found, {len(search_results)} returned")
            
            if count == 0:
                print(f"  ❌ FAILED: Returned 0 results")
                results.append({
                    'test': test_case['name'],
                    'status': 'FAILED',
                    'reason': 'Returned 0 results',
                    'count': count
                })
            else:
                print(f"  ✅ PASSED: Returned {count} results")
                results.append({
                    'test': test_case['name'],
                    'status': 'PASSED',
                    'count': count
                })
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                'test': test_case['name'],
                'status': 'ERROR',
                'error': str(e)
            })
        
        print()
    
    # Compare results for AND logic
    print("=" * 80)
    print("AND LOGIC VERIFICATION")
    print("=" * 80)
    print()
    
    single_person_count = None
    multiple_count = None
    
    for result in results:
        if 'פניות מאור גלילי' in result.get('test', ''):
            single_person_count = result.get('count', 0)
        if 'מסוג 10' in result.get('test', '') and 'Multiple' in result.get('test', ''):
            multiple_count = result.get('count', 0)
    
    if single_person_count is not None and multiple_count is not None:
        print(f"Single entity (person): {single_person_count} results")
        print(f"Multiple entities (person + type): {multiple_count} results")
        
        if multiple_count < single_person_count:
            print(f"✅ AND LOGIC WORKS: Multiple filters = fewer results ({multiple_count} < {single_person_count})")
        elif multiple_count == single_person_count:
            print(f"⚠️  AND LOGIC: Same count (might be correct if all person results have type 10)")
        else:
            print(f"❌ AND LOGIC FAILED: Multiple filters = more results ({multiple_count} > {single_person_count})")
    
    search_service.close()
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for r in results if r.get('status') == 'PASSED')
    failed = sum(1 for r in results if r.get('status') in ['FAILED', 'ERROR'])
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    
    return failed == 0

if __name__ == "__main__":
    success = test_and_logic()
    sys.exit(0 if success else 1)

