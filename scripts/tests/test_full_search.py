"""Test full search with multiple entities."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def test_full_search():
    """Test full search."""
    search_service = SearchService()
    search_service.connect_db()
    
    try:
        query = "בקשות מאור גלילי מסוג 4"
        print(f"Testing: {query}")
        results, count = search_service.search(query, top_k=20)
        print(f"✅ Success: Count={count}, Returned={len(results)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        search_service.close()

if __name__ == "__main__":
    test_full_search()

