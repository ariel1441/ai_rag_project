"""Debug type query to see what's happening."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv
import json

load_dotenv()

# Test query parsing
query = "בקשות מסוג 10"
config_path = project_root / "config" / "search_config.json"
config = None
if config_path.exists():
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

search_service = SearchService()
search_service.connect_db()

# Parse query
parsed = search_service.query_parser.parse(query)
print(f"Query: {query}")
print(f"Parsed: {json.dumps(parsed, indent=2, ensure_ascii=False)}")

# Check if type_id exists in DB
if 'type_id' in parsed.get('entities', {}):
    type_id = parsed['entities']['type_id']
    print(f"\nExtracted type_id: {type_id}")
    
    # Check DB
    search_service.cursor.execute("""
        SELECT COUNT(*) FROM requests WHERE requesttypeid::TEXT = %s::TEXT
    """, (str(type_id),))
    db_count = search_service.cursor.fetchone()[0]
    print(f"DB count for type_id {type_id}: {db_count}")
    
    # Try search
    results, count = search_service.search(query, top_k=20)
    print(f"Search count: {count}")
    print(f"Results returned: {len(results)}")
else:
    print("\n❌ type_id not extracted!")

search_service.close()

