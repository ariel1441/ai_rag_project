"""Debug why AND logic isn't working for person + type."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def debug_and_logic():
    """Debug AND logic."""
    search_service = SearchService()
    search_service.connect_db()
    
    query1 = "פניות מאור גלילי"
    query2 = "בקשות מאור גלילי מסוג 4"
    
    print("Query 1 (single):", query1)
    results1, count1 = search_service.search(query1, top_k=20)
    print(f"  Count: {count1}")
    print()
    
    print("Query 2 (multiple):", query2)
    results2, count2 = search_service.search(query2, top_k=20)
    print(f"  Count: {count2}")
    print()
    
    # Parse query 2
    parsed = search_service.query_parser.parse(query2)
    print("Parsed entities:", parsed.get('entities'))
    
    # Check if text filter should be applied
    entities = parsed.get('entities', {})
    structured_entities = ['type_id', 'status_id', 'date_range']
    text_entities = ['person_name', 'project_name']
    
    has_structured = any(
        key in entities and (key != 'urgency' or entities.get('urgency', False))
        for key in structured_entities
    ) or (entities.get('urgency', False) is True)
    
    has_text = any(key in entities for key in text_entities)
    has_multiple = (has_structured and has_text) or (len([k for k in text_entities if k in entities]) > 1)
    
    print(f"has_structured: {has_structured}")
    print(f"has_text: {has_text}")
    print(f"has_multiple: {has_multiple}")
    
    if count2 >= count1:
        print(f"\n❌ AND LOGIC FAILED: {count2} >= {count1} (should be less)")
    else:
        print(f"\n✅ AND LOGIC WORKS: {count2} < {count1}")
    
    search_service.close()

if __name__ == "__main__":
    debug_and_logic()

