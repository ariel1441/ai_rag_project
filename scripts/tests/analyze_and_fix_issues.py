"""
Analyze test results and identify real issues vs test issues.
Then test fixes before implementing.
"""
import os
import sys
from pathlib import Path
import psycopg2
from pgvector.psycopg2 import register_vector
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from scripts.utils.query_parser import QueryParser
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    
    conn = psycopg2.connect(
        host=host, port=int(port), database=database,
        user=user, password=password
    )
    register_vector(conn)
    return conn

def analyze_issues():
    """Analyze what's actually broken."""
    print("=" * 80)
    print("ANALYZING ISSUES")
    print("=" * 80)
    print()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Issue 1: Check "אור גלילי" - is it person or project?
    print("ISSUE 1: אור גלילי - Person or Project?")
    print("-" * 80)
    
    # Check person fields
    cursor.execute("""
        SELECT COUNT(DISTINCT requestid)
        FROM requests
        WHERE 
            LOWER(COALESCE(updatedby, '')) LIKE '%אור גלילי%' OR
            LOWER(COALESCE(createdby, '')) LIKE '%אור גלילי%' OR
            LOWER(COALESCE(responsibleemployeename, '')) LIKE '%אור גלילי%'
    """)
    person_count = cursor.fetchone()[0]
    
    # Check projectname
    cursor.execute("""
        SELECT COUNT(DISTINCT requestid)
        FROM requests
        WHERE LOWER(COALESCE(projectname, '')) LIKE '%אור גלילי%'
    """)
    project_count = cursor.fetchone()[0]
    
    print(f"  In person fields: {person_count}")
    print(f"  In projectname: {project_count}")
    
    if person_count == 0 and project_count > 0:
        print("  ✅ CONCLUSION: It's a PROJECT name, not person")
        print("  ✅ Search is CORRECT (finds it in projectname)")
        print("  ❌ Test is WRONG (checks person fields only)")
    elif person_count > 0:
        print("  ✅ CONCLUSION: It's a PERSON name")
    else:
        print("  ⚠️  CONCLUSION: Not found anywhere (semantic search only)")
    print()
    
    # Issue 2: Check why general queries return 0
    print("ISSUE 2: Why do general queries return 0?")
    print("-" * 80)
    
    test_queries = [
        "תיאום תכנון",
        "תכנון",
        "בקשות דחופות",
        "אלינור",
    ]
    
    config_path = project_root / "config" / "search_config.json"
    config = None
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    search_service = SearchService()
    search_service.connect_db()
    
    for query in test_queries:
        try:
            results, count = search_service.search(query, top_k=20)
            print(f"  '{query}': {count} results")
            
            if count == 0:
                # Check if query has similarity threshold issue
                parsed = search_service.query_parser.parse(query)
                print(f"    Intent: {parsed.get('intent')}, Type: {parsed.get('query_type')}")
        except Exception as e:
            print(f"  '{query}': ERROR - {str(e)}")
    
    search_service.close()
    print()
    
    # Issue 3: Check person queries that work
    print("ISSUE 3: Person queries - which work?")
    print("-" * 80)
    
    person_queries = [
        ("מיניב ליבוביץ", "יניב ליבוביץ"),
        ("מאוקסנה כלפון", "אוקסנה כלפון"),
        ("ממשה אוגלבו", "משה אוגלבו"),
    ]
    
    for query_text, person_name in person_queries:
        # Check DB
        cursor.execute("""
            SELECT COUNT(DISTINCT requestid)
            FROM requests
            WHERE 
                LOWER(COALESCE(updatedby, '')) LIKE %s OR
                LOWER(COALESCE(createdby, '')) LIKE %s OR
                LOWER(COALESCE(responsibleemployeename, '')) LIKE %s
        """, (f'%{person_name.lower()}%', f'%{person_name.lower()}%', f'%{person_name.lower()}%'))
        db_count = cursor.fetchone()[0]
        
        # Check search
        search_service = SearchService()
        search_service.connect_db()
        results, search_count = search_service.search(query_text, top_k=20)
        search_service.close()
        
        ratio = search_count / db_count if db_count > 0 else 0
        status = "✅" if 0.3 <= ratio <= 3.0 else "⚠️"
        print(f"  {status} '{query_text}': DB={db_count}, Search={search_count}, Ratio={ratio:.2f}")
    print()
    
    # Issue 4: Check why some queries return 0
    print("ISSUE 4: Queries returning 0 results")
    print("-" * 80)
    
    zero_queries = [
        "בקשות דחופות",
        "פניות אחרונות",
        "בנייה",
        "אישור",
    ]
    
    search_service = SearchService()
    search_service.connect_db()
    
    for query in zero_queries:
        results, count = search_service.search(query, top_k=20)
        if count == 0:
            # Check if it's a similarity threshold issue
            # Try with lower threshold by checking embeddings directly
            print(f"  '{query}': 0 results")
            print(f"    This might be similarity threshold too high")
            print(f"    Or query doesn't match any embeddings semantically")
    
    search_service.close()
    print()
    
    cursor.close()
    conn.close()
    
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    analyze_issues()

