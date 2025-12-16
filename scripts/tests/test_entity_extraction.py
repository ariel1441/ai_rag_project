"""Test entity extraction for multiple entities."""
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

def test_entity_extraction():
    """Test that all entities are extracted."""
    search_service = SearchService()
    
    query = "בקשות מאור גלילי מסוג 4"
    parsed = search_service.query_parser.parse(query)
    
    print(f"Query: {query}")
    print(f"Parsed entities: {json.dumps(parsed.get('entities'), indent=2, ensure_ascii=False)}")
    print(f"Intent: {parsed.get('intent')}")
    
    entities = parsed.get('entities', {})
    has_person = 'person_name' in entities
    has_type = 'type_id' in entities
    
    print(f"\nHas person_name: {has_person}")
    print(f"Has type_id: {has_type}")
    
    if has_person and has_type:
        print(f"\n✅ Both entities extracted!")
        print(f"  person_name: {entities.get('person_name')}")
        print(f"  type_id: {entities.get('type_id')}")
    else:
        print(f"\n❌ Missing entities!")
        if not has_person:
            print(f"  Missing: person_name")
        if not has_type:
            print(f"  Missing: type_id")

if __name__ == "__main__":
    test_entity_extraction()

