"""Test fixed AND logic with valid queries."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def test_queries():
    """Test various queries to verify AND logic works."""
    print("=" * 80)
    print("TESTING FIXED AND LOGIC")
    print("=" * 80)
    print()
    
    search_service = SearchService()
    search_service.connect_db()
    
    # First, find a valid type_id
    search_service.cursor.execute("""
        SELECT requesttypeid, COUNT(*) as cnt
        FROM requests
        GROUP BY requesttypeid
        ORDER BY cnt DESC
        LIMIT 5
    """)
    valid_types = search_service.cursor.fetchall()
    print("Valid type_ids in database:")
    for type_id, count in valid_types:
        print(f"  Type {type_id}: {count} requests")
    print()
    
    # Test queries
    test_cases = [
        {
            'name': 'Single entity - person',
            'query': 'פניות מאור גלילי',
            'should_work': True,
        },
        {
            'name': 'Single entity - person (valid)',
            'query': 'פניות מיניב ליבוביץ',
            'should_work': True,
        },
        {
            'name': 'Single entity - type (valid)',
            'query': f'בקשות מסוג {valid_types[0][0]}',
            'should_work': True,
        },
        {
            'name': 'Single entity - status',
            'query': 'בקשות בסטטוס 1',
            'should_work': True,
        },
        {
            'name': 'Multiple entities - person + type',
            'query': f'בקשות מאור גלילי מסוג {valid_types[0][0]}',
            'should_work': True,
            'should_be_less': 'פניות מאור גלילי',
        },
        {
            'name': 'Multiple entities - person + status',
            'query': 'פניות מיניב ליבוביץ בסטטוס 1',
            'should_work': True,
        },
    ]
    
    results = {}
    all_passed = True
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        print(f"  Query: {test_case['query']}")
        
        try:
            search_results, count = search_service.search(test_case['query'], top_k=20)
            print(f"  Results: {count} found, {len(search_results)} returned")
            
            if count == 0 and test_case['should_work']:
                print(f"  ❌ FAILED: Returned 0 results (should work)")
                all_passed = False
            elif count > 0:
                print(f"  ✅ PASSED: Returned {count} results")
            else:
                print(f"  ⚠️  Returned 0 (might be expected)")
            
            results[test_case['name']] = count
            
            # Check AND logic
            if 'should_be_less' in test_case:
                single_query = test_case['should_be_less']
                single_count = results.get(single_query, None)
                if single_count is not None:
                    if count < single_count:
                        print(f"  ✅ AND LOGIC WORKS: {count} < {single_count}")
                    else:
                        print(f"  ❌ AND LOGIC FAILED: {count} >= {single_count}")
                        all_passed = False
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            all_passed = False
        
        print()
    
    search_service.close()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    return all_passed

if __name__ == "__main__":
    success = test_queries()
    sys.exit(0 if success else 1)

