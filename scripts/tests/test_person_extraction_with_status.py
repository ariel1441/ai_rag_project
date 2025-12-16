"""Test person name extraction when status is present."""
import os
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def test_extraction():
    """Test person name extraction."""
    search_service = SearchService()
    
    query = "פניות מיניב ליבוביץ בסטטוס 1"
    parsed = search_service.query_parser.parse(query)
    
    print(f"Query: {query}")
    print(f"Parsed: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
    
    entities = parsed.get('entities', {})
    person_name = entities.get('person_name')
    status_id = entities.get('status_id')
    
    print(f"\nPerson name extracted: {person_name}")
    print(f"Status ID extracted: {status_id}")
    
    if person_name and 'בסטטוס' in person_name:
        print(f"\n❌ Person name extraction is WRONG - includes 'בסטטוס'")
    elif person_name == 'יניב ליבוביץ':
        print(f"\n✅ Person name extraction is CORRECT")
    else:
        print(f"\n⚠️  Person name: '{person_name}' (might be wrong)")

if __name__ == "__main__":
    test_extraction()

