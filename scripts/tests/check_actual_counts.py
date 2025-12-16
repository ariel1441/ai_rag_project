"""Check actual counts from database vs search results."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv
import psycopg2
from pgvector.psycopg2 import register_vector

load_dotenv()

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        database=os.getenv("POSTGRES_DATABASE", "ai_requests_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

def check_counts():
    """Check actual counts."""
    print("=" * 80)
    print("CHECKING ACTUAL COUNTS: DB vs SEARCH")
    print("=" * 80)
    print()
    
    # Database counts (exact SQL)
    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor()
    
    # Test queries
    test_cases = [
        ("בקשות בסטטוס 1", "requeststatusid::TEXT = '1'::TEXT"),
        ("בקשות מסוג 4", "requesttypeid::TEXT = '4'::TEXT"),
    ]
    
    search_service = SearchService()
    search_service.connect_db()
    
    for query, sql_filter in test_cases:
        print(f"Query: {query}")
        print("-" * 80)
        
        # 1. Exact SQL count (no similarity threshold)
        cursor.execute(f"""
            SELECT COUNT(DISTINCT requestid) FROM requests WHERE {sql_filter}
        """)
        exact_sql_count = cursor.fetchone()[0]
        print(f"1. Exact SQL count (no similarity): {exact_sql_count}")
        
        # 2. Search count (with similarity threshold)
        try:
            results, search_count = search_service.search(query, top_k=20)
            print(f"2. Search count (with similarity threshold): {search_count}")
            print(f"   Results returned: {len(results)}")
        except Exception as e:
            print(f"2. Search error: {str(e)}")
            search_count = 0
        
        # 3. Check what similarity threshold is being used
        parsed = search_service.query_parser.parse(query)
        intent = parsed.get('intent', 'general')
        entities = parsed.get('entities', {})
        
        # Determine threshold
        structured_entities = ['type_id', 'status_id', 'date_range']
        text_entities = ['person_name', 'project_name']
        has_structured = any(
            key in entities and (key != 'urgency' or entities.get('urgency', False))
            for key in structured_entities
        ) or (entities.get('urgency', False) is True)
        has_text = any(key in entities for key in text_entities)
        has_multiple = (has_structured and has_text) or (len([k for k in text_entities if k in entities]) > 1)
        
        if has_multiple and has_structured and has_text:
            threshold = 0.2
        elif intent in ['person', 'project']:
            threshold = 0.5
        else:
            threshold = 0.4
        
        print(f"3. Similarity threshold used: {threshold}")
        print(f"4. Intent: {intent}")
        print(f"5. Has multiple entities: {has_multiple}")
        
        # 4. Count with similarity threshold (manual check)
        # Generate embedding for query
        model = search_service._get_embedding_model()
        query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
        
        # Insert into temp table
        cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
        cursor.execute("CREATE TEMP TABLE temp_query_embedding (embedding vector(384));")
        cursor.execute("INSERT INTO temp_query_embedding (embedding) VALUES (%s);", (query_embedding.tolist(),))
        
        # Count with similarity threshold
        if 'status' in sql_filter:
            join_sql = "INNER JOIN requests r ON e.requestid = r.requestid"
            where_clause = f"WHERE e.embedding IS NOT NULL AND r.{sql_filter.split('=')[0].strip()} = {sql_filter.split('=')[1].strip()}"
        else:
            join_sql = "INNER JOIN requests r ON e.requestid = r.requestid"
            where_clause = f"WHERE e.embedding IS NOT NULL AND r.{sql_filter.split('=')[0].strip()} = {sql_filter.split('=')[1].strip()}"
        
        # Fix the SQL filter format
        if 'requeststatusid' in sql_filter:
            filter_part = "r.requeststatusid::TEXT = '1'::TEXT"
        elif 'requesttypeid' in sql_filter:
            filter_part = "r.requesttypeid::TEXT = '4'::TEXT"
        else:
            filter_part = sql_filter.replace('requestid', 'r.requestid')
        
        cursor.execute(f"""
            SELECT COUNT(DISTINCT e.requestid)
            FROM request_embeddings e
            INNER JOIN requests r ON e.requestid = r.requestid
            CROSS JOIN temp_query_embedding t
            WHERE e.embedding IS NOT NULL
            AND {filter_part}
            AND (1 - (e.embedding <=> t.embedding)) >= {threshold}
        """)
        threshold_count = cursor.fetchone()[0]
        print(f"6. Count with similarity threshold ({threshold}): {threshold_count}")
        
        # 5. Count without similarity threshold (just SQL filter)
        cursor.execute(f"""
            SELECT COUNT(DISTINCT e.requestid)
            FROM request_embeddings e
            INNER JOIN requests r ON e.requestid = r.requestid
            WHERE e.embedding IS NOT NULL
            AND {filter_part}
        """)
        no_threshold_count = cursor.fetchone()[0]
        print(f"7. Count without similarity threshold (just SQL filter): {no_threshold_count}")
        
        print()
        print(f"Summary:")
        print(f"  - Exact SQL (no embeddings): {exact_sql_count}")
        print(f"  - With embeddings, no threshold: {no_threshold_count}")
        print(f"  - With embeddings + threshold ({threshold}): {threshold_count}")
        print(f"  - Search returned: {search_count}")
        print()
        
        if search_count != threshold_count:
            print(f"⚠️  MISMATCH: Search count ({search_count}) != Threshold count ({threshold_count})")
        else:
            print(f"✅ Match: Search count = Threshold count")
        
        print()
        print("=" * 80)
        print()
    
    cursor.close()
    conn.close()
    search_service.close()

if __name__ == "__main__":
    check_counts()

