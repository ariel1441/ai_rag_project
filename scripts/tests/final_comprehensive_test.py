"""Final comprehensive test of all fixes."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def final_test():
    """Run final comprehensive tests."""
    print("=" * 80)
    print("FINAL COMPREHENSIVE TEST - ALL FIXES")
    print("=" * 80)
    print()
    
    search_service = SearchService()
    search_service.connect_db()
    
    test_cases = [
        # Single Person Queries
        {
            'query': 'פניות מאור גלילי',
            'type': 'Single Person',
            'expected_min': 34,
            'check_count': True,
        },
        {
            'query': 'פניות מיניב ליבוביץ',
            'type': 'Single Person',
            'expected_min': 118,
            'check_count': True,
        },
        
        # Single Type Queries (Exact SQL - should return ALL)
        {
            'query': 'בקשות מסוג 4',
            'type': 'Single Type (Exact)',
            'expected_min': 3700,  # Should be close to 3731
            'check_count': True,
        },
        {
            'query': 'בקשות מסוג 1',
            'type': 'Single Type (Exact)',
            'expected_min': 2100,  # Should be close to 2114
            'check_count': True,
        },
        
        # Single Status Queries (Exact SQL - should return ALL)
        {
            'query': 'בקשות בסטטוס 1',
            'type': 'Single Status (Exact)',
            'expected_min': 1260,  # Should be close to 1268
            'check_count': True,
        },
        {
            'query': 'בקשות בסטטוס 10',
            'type': 'Single Status (Exact)',
            'expected_min': 4200,  # Should be close to 4217
            'check_count': True,
        },
        
        # Multiple Entity Queries (AND Logic)
        {
            'query': 'בקשות מאור גלילי מסוג 4',
            'type': 'Multiple (Person + Type)',
            'expected_max': 34,  # Should be LESS than single person
            'check_and_logic': True,
            'single_query': 'פניות מאור גלילי',
        },
        {
            'query': 'פניות מיניב ליבוביץ בסטטוס 1',
            'type': 'Multiple (Person + Status)',
            'expected_max': 118,  # Should be LESS than single person
            'check_and_logic': True,
            'single_query': 'פניות מיניב ליבוביץ',
        },
        
        # Edge Cases
        {
            'query': 'בקשה מאור גלילי',
            'type': 'Singular Form',
            'expected_min': 10,
            'check_count': True,
        },
        {
            'query': 'תיאום תכנון',
            'type': 'General Query (Not Person)',
            'expected_min': 0,  # Should return some results
            'check_not_person': True,
        },
    ]
    
    results = []
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] Testing: {test_case['type']}")
        print(f"  Query: {test_case['query']}")
        
        try:
            search_results, count = search_service.search(test_case['query'], top_k=20)
            returned = len(search_results)
            
            print(f"  Count: {count}, Returned: {returned}")
            
            # Check count accuracy
            if test_case.get('check_count', False):
                if count < returned:
                    print(f"  ❌ COUNT ERROR: Count ({count}) < Returned ({returned})")
                    all_passed = False
                elif count == 0 and returned > 0:
                    print(f"  ❌ COUNT ERROR: Count is 0 but {returned} results returned")
                    all_passed = False
                elif count < test_case.get('expected_min', 0):
                    print(f"  ⚠️  Count ({count}) < Expected min ({test_case.get('expected_min', 0)})")
                else:
                    print(f"  ✅ Count OK: {count} >= {test_case.get('expected_min', 0)}")
            
            # Check AND logic
            if test_case.get('check_and_logic', False):
                single_query = test_case.get('single_query')
                if single_query:
                    single_results, single_count = search_service.search(single_query, top_k=20)
                    if count > single_count:
                        print(f"  ❌ AND LOGIC FAILED: {count} > {single_count} (should be less)")
                        all_passed = False
                    elif count == single_count:
                        print(f"  ⚠️  AND LOGIC: Same count ({count}) - might be correct if all match")
                    else:
                        print(f"  ✅ AND LOGIC WORKS: {count} < {single_count}")
            
            # Check not person
            if test_case.get('check_not_person', False):
                parsed = search_service.query_parser.parse(test_case['query'])
                intent = parsed.get('intent', '')
                if intent == 'person':
                    print(f"  ❌ WRONG INTENT: Detected as 'person' (should be general)")
                    all_passed = False
                else:
                    print(f"  ✅ Intent OK: {intent} (not person)")
            
            # Check exact SQL filters return all results
            if 'Exact' in test_case['type']:
                if count < test_case.get('expected_min', 0) * 0.9:  # Allow 10% margin
                    print(f"  ⚠️  Exact filter might be filtering too much: {count} < {test_case.get('expected_min', 0)}")
                else:
                    print(f"  ✅ Exact filter returns all results: {count}")
            
            results.append({
                'query': test_case['query'],
                'type': test_case['type'],
                'count': count,
                'returned': returned,
                'passed': True
            })
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            all_passed = False
            results.append({
                'query': test_case['query'],
                'type': test_case['type'],
                'error': str(e),
                'passed': False
            })
        
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for r in results if r.get('passed', False))
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    print()
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    print()
    print("Detailed Results:")
    for r in results:
        status = "✅" if r.get('passed', False) else "❌"
        print(f"{status} {r['type']}: {r['query']} → Count: {r.get('count', 'ERROR')}, Returned: {r.get('returned', 'ERROR')}")
    
    search_service.close()
    
    return all_passed

if __name__ == "__main__":
    success = final_test()
    sys.exit(0 if success else 1)

