"""Comprehensive test of all fixes."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def comprehensive_test():
    """Test all fixes comprehensively."""
    print("=" * 80)
    print("COMPREHENSIVE TEST - ALL FIXES")
    print("=" * 80)
    print()
    
    search_service = SearchService()
    search_service.connect_db()
    
    test_cases = [
        # Single entity - should work
        ("פניות מיניב ליבוביץ", "Single person", True),
        ("פניות מאור גלילי", "Single person", True),
        ("בקשות מסוג 4", "Single type", True),
        ("בקשות בסטטוס 1", "Single status", True),
        
        # Multiple entities - AND logic
        ("בקשות מאור גלילי מסוג 4", "Person + Type", False),  # Might be 0 (no matches)
        ("פניות מיניב ליבוביץ בסטטוס 1", "Person + Status", True),
    ]
    
    results = []
    all_passed = True
    
    for query, description, should_have_results in test_cases:
        print(f"Testing: {description}")
        print(f"  Query: {query}")
        
        try:
            search_results, count = search_service.search(query, top_k=20)
            returned = len(search_results)
            
            print(f"  Count: {count}, Returned: {returned}")
            
            if should_have_results and count == 0:
                print(f"  ❌ FAILED: Should have results but got 0")
                all_passed = False
            elif not should_have_results and count == 0:
                print(f"  ✅ PASSED: 0 results (expected - no matches in DB)")
            elif count > 0:
                print(f"  ✅ PASSED: {count} results")
            else:
                print(f"  ⚠️  Got 0 results")
            
            # Check count accuracy
            if count < returned:
                print(f"  ❌ COUNT ERROR: Count ({count}) < Returned ({returned})")
                all_passed = False
            elif count == 0 and returned > 0:
                print(f"  ❌ COUNT ERROR: Count is 0 but {returned} results returned")
                all_passed = False
            
            results.append({
                'query': query,
                'description': description,
                'count': count,
                'returned': returned,
                'passed': count > 0 if should_have_results else True
            })
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            all_passed = False
        
        print()
    
    # Test AND logic
    print("=" * 80)
    print("AND LOGIC VERIFICATION")
    print("=" * 80)
    print()
    
    single_person = next((r for r in results if r['query'] == 'פניות מאור גלילי'), None)
    multiple_person_type = next((r for r in results if r['query'] == 'בקשות מאור גלילי מסוג 4'), None)
    
    if single_person and multiple_person_type:
        print(f"Single: {single_person['count']} results")
        print(f"Multiple: {multiple_person_type['count']} results")
        
        if multiple_person_type['count'] < single_person['count']:
            print(f"✅ AND LOGIC WORKS: {multiple_person_type['count']} < {single_person['count']}")
        elif multiple_person_type['count'] == 0:
            print(f"✅ AND LOGIC: 0 results (no matches in DB - correct)")
        else:
            print(f"❌ AND LOGIC FAILED: {multiple_person_type['count']} >= {single_person['count']}")
            all_passed = False
    
    search_service.close()
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    return all_passed

if __name__ == "__main__":
    success = comprehensive_test()
    sys.exit(0 if success else 1)

