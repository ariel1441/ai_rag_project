"""Test count accuracy - count should match returned results."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def test_count_accuracy():
    """Test that count matches returned results."""
    print("=" * 80)
    print("TESTING COUNT ACCURACY")
    print("=" * 80)
    print()
    
    search_service = SearchService()
    search_service.connect_db()
    
    test_queries = [
        "פניות מיניב ליבוביץ",
        "פניות מאור גלילי",
        "בקשה מאור גלילי",  # Singular
        "בקשות מסוג 4",
        "בקשות בסטטוס 1",
    ]
    
    all_correct = True
    
    for query in test_queries:
        print(f"Testing: {query}")
        try:
            results, count = search_service.search(query, top_k=20)
            returned = len(results)
            
            print(f"  Count reported: {count}")
            print(f"  Results returned: {returned}")
            
            # Count should be >= returned (count is total, returned is limited to top_k)
            if count == 0 and returned > 0:
                print(f"  ❌ FAILED: Count is 0 but {returned} results returned!")
                all_correct = False
            elif count < returned:
                print(f"  ❌ FAILED: Count ({count}) < Returned ({returned})")
                all_correct = False
            elif count == returned:
                print(f"  ✅ PASSED: Count matches returned ({count})")
            else:
                print(f"  ✅ PASSED: Count ({count}) >= Returned ({returned}) - correct")
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            all_correct = False
        
        print()
    
    search_service.close()
    
    print("=" * 80)
    if all_correct:
        print("✅ All counts are correct!")
    else:
        print("❌ Some counts are incorrect - need to fix")
    
    return all_correct

if __name__ == "__main__":
    success = test_count_accuracy()
    sys.exit(0 if success else 1)

