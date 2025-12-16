"""
Comprehensive Search Accuracy Test

Tests search accuracy by comparing results with actual database queries.
Tests all demo questions and more, verifying:
- Query parsing (intent, entities)
- Search results accuracy
- Result counts vs actual DB counts
- Person name extraction
- Query type detection
"""
import os
import sys
from pathlib import Path
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from scripts.utils.query_parser import QueryParser
from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

# Test queries
TEST_QUERIES = [
    # Person queries
    ("פניות מאור גלילי", "person", "אור גלילי"),
    ("פניות מיניב ליבוביץ", "person", "יניב ליבוביץ"),
    ("כמה פניות יש מאור גלילי?", "person", "אור גלילי"),
    ("כמה פניות יש מיניב ליבוביץ?", "person", "יניב ליבוביץ"),
    
    # General queries (should NOT be person)
    ("תיאום תכנון", "general", None),
    ("בקשות מסוג 4", "type", None),
    ("כמה פניות יש מסוג 4", "count", None),
    
    # Similar queries
    ("פניות דומות ל221000226", "similar", "221000226"),
    
    # Project queries
    ("פרויקטים של X", "project", None),
]

def get_db_connection():
    """Get database connection."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    
    if not password:
        raise ValueError("POSTGRES_PASSWORD not in .env!")
    
    conn = psycopg2.connect(
        host=host, port=int(port), database=database,
        user=user, password=password
    )
    register_vector(conn)
    return conn

def count_requests_by_person(conn, person_name):
    """Count requests where person name appears in relevant fields."""
    cursor = conn.cursor()
    
    # Search in updatedby, createdby, responsibleemployeename
    cursor.execute("""
        SELECT COUNT(DISTINCT requestid)
        FROM requests
        WHERE 
            LOWER(updatedby) LIKE %s OR
            LOWER(createdby) LIKE %s OR
            LOWER(responsibleemployeename) LIKE %s
    """, (f'%{person_name.lower()}%', f'%{person_name.lower()}%', f'%{person_name.lower()}%'))
    
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def count_requests_by_type(conn, type_id):
    """Count requests by type ID."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM requests
        WHERE requesttypeid::TEXT = %s
    """, (str(type_id),))
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def test_query_parsing():
    """Test query parsing accuracy."""
    print("=" * 80)
    print("TEST 1: Query Parsing")
    print("=" * 80)
    
    config_path = project_root / "config" / "search_config.json"
    config = None
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    parser = QueryParser(config)
    
    all_passed = True
    for query, expected_intent, expected_entity in TEST_QUERIES:
        parsed = parser.parse(query)
        intent = parsed.get('intent', 'unknown')
        query_type = parsed.get('query_type', 'unknown')
        entities = parsed.get('entities', {})
        
        # Check intent
        intent_ok = intent == expected_intent
        if not intent_ok:
            print(f"❌ Query: '{query}'")
            print(f"   Expected intent: {expected_intent}, Got: {intent}")
            all_passed = False
        
        # Check entity extraction
        entity_ok = True
        if expected_entity:
            if expected_intent == 'person':
                entity_ok = entities.get('person_name') == expected_entity
                if not entity_ok:
                    print(f"❌ Query: '{query}'")
                    print(f"   Expected person_name: '{expected_entity}', Got: '{entities.get('person_name')}'")
                    all_passed = False
            elif expected_intent == 'similar':
                entity_ok = entities.get('request_id') == expected_entity
                if not entity_ok:
                    print(f"❌ Query: '{query}'")
                    print(f"   Expected request_id: '{expected_entity}', Got: '{entities.get('request_id')}'")
                    all_passed = False
        
        if intent_ok and entity_ok:
            print(f"✅ Query: '{query}'")
            print(f"   Intent: {intent}, Type: {query_type}, Entities: {entities}")
    
    print()
    return all_passed

def test_search_accuracy():
    """Test search accuracy against database."""
    print("=" * 80)
    print("TEST 2: Search Accuracy vs Database")
    print("=" * 80)
    
    conn = get_db_connection()
    config_path = project_root / "config" / "search_config.json"
    config = None
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    search_service = SearchService()
    search_service.connect_db()
    
    all_passed = True
    
    # Test person queries
    person_queries = [
        ("פניות מאור גלילי", "אור גלילי"),
        ("פניות מיניב ליבוביץ", "יניב ליבוביץ"),
    ]
    
    for query, person_name in person_queries:
        print(f"\nTesting: '{query}'")
        print(f"Expected person name: '{person_name}'")
        
        # Get actual DB count
        db_count = count_requests_by_person(conn, person_name)
        print(f"Database count (LIKE query): {db_count}")
        
        # Get search results
        results, search_count = search_service.search(query, top_k=20)
        print(f"Search count: {search_count}")
        print(f"Results returned: {len(results)}")
        
        # Check if results are reasonable
        # Semantic search might find more/less than exact LIKE, but should be close
        ratio = search_count / db_count if db_count > 0 else 0
        if 0.5 <= ratio <= 2.0:  # Within 50%-200% is acceptable for semantic search
            print(f"✅ Count ratio: {ratio:.2f} (acceptable)")
        else:
            print(f"⚠️  Count ratio: {ratio:.2f} (might need investigation)")
            if ratio < 0.3 or ratio > 3.0:
                all_passed = False
        
        # Check if person name appears in results
        person_found = False
        for result in results[:5]:  # Check top 5
            req_id = result.get('requestid')
            if req_id:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT updatedby, createdby, responsibleemployeename
                    FROM requests
                    WHERE requestid = %s
                """, (req_id,))
                row = cursor.fetchone()
                cursor.close()
                if row:
                    fields = ' '.join([str(f) or '' for f in row]).lower()
                    if person_name.lower() in fields:
                        person_found = True
                        break
        
        if person_found:
            print(f"✅ Person name found in top results")
        else:
            print(f"⚠️  Person name not found in top 5 results")
    
    # Test type queries
    print(f"\nTesting: 'כמה פניות יש מסוג 4'")
    db_count = count_requests_by_type(conn, 4)
    print(f"Database count (exact match): {db_count}")
    
    results, search_count = search_service.search("כמה פניות יש מסוג 4", top_k=20)
    print(f"Search count: {search_count}")
    
    if search_count == db_count:
        print(f"✅ Count matches database exactly")
    else:
        print(f"⚠️  Count differs: DB={db_count}, Search={search_count}")
        if abs(search_count - db_count) > 10:
            all_passed = False
    
    conn.close()
    search_service.close()
    print()
    return all_passed

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SEARCH ACCURACY TEST")
    print("=" * 80 + "\n")
    
    results = []
    
    # Test 1: Query Parsing
    results.append(("Query Parsing", test_query_parsing()))
    
    # Test 2: Search Accuracy
    results.append(("Search Accuracy", test_search_accuracy()))
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    print()
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Review output above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

