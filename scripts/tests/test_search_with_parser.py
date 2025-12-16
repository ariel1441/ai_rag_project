"""
Test version of search.py with hardcoded queries - no user input required.
Tests the query parser integration with multiple queries.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import os
import sys
import re
import json
from pathlib import Path

# Import query parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.query_parser import parse_query

# Fix Hebrew RTL display
def fix_hebrew_rtl(text):
    if not text:
        return text
    pattern = r'([\u0590-\u05FF]+|[^\u0590-\u05FF]+)'
    parts = re.findall(pattern, str(text))
    result = []
    for part in parts:
        if re.match(r'[\u0590-\u05FF]+', part):
            result.append(part[::-1])
        else:
            result.append(part)
    return ''.join(result)

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Test queries
TEST_QUERIES = [
    "פניות מאור גלילי",
    "בקשות מסוג 4",
    "פרויקט אלינור",
    "אלינור",
    "כמה פניות יש מיניב ליבוביץ"
]

def run_search_test(query: str, config: dict):
    """Run a single search test."""
    print("=" * 80)
    print(f"TEST QUERY: {fix_hebrew_rtl(query)}")
    print("=" * 80)
    print()
    
    try:
        # Parse query
        print("Parsing query...")
        parsed = parse_query(query, config)
        print(f"✓ Intent: {parsed['intent']}")
        if parsed['entities']:
            print(f"✓ Entities: {parsed['entities']}")
        if parsed['target_fields']:
            print(f"✓ Target fields: {', '.join(parsed['target_fields'][:3])}...")
        print()
        
        # Connection
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        if not password:
            print("ERROR: POSTGRES_PASSWORD not in .env!")
            return False
        
        conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
        register_vector(conn)
        cursor = conn.cursor()
        
        # Apply filters from parser
        sql_filters = []
        filter_params = []
        
        if 'type_id' in parsed['entities']:
            type_id = parsed['entities']['type_id']
            sql_filters.append("r.requesttypeid::TEXT = %s::TEXT")
            filter_params.append(str(type_id))
            print(f"✓ Filter: requesttypeid = {type_id}")
        
        if 'status_id' in parsed['entities']:
            status_id = parsed['entities']['status_id']
            sql_filters.append("r.requeststatusid::TEXT = %s::TEXT")
            filter_params.append(str(status_id))
            print(f"✓ Filter: requeststatusid = {status_id}")
        
        request_filter_sql = ""
        if sql_filters:
            request_filter_sql = "WHERE " + " AND ".join(sql_filters)
            print()
        
        # Generate embedding
        print("Generating embedding...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
        print(f"✓ Embedding generated: {len(query_embedding)} dimensions")
        print()
        
        # Insert into temp table
        print("Preparing search...")
        cursor.execute("""
            CREATE TEMP TABLE temp_query_embedding (
                id SERIAL PRIMARY KEY,
                embedding vector(384)
            );
        """)
        
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        cursor.execute("""
            INSERT INTO temp_query_embedding (embedding)
            VALUES (%s::vector);
        """, (embedding_str,))
        
        conn.commit()
        print("✓ Ready to search")
        print()
        
        # Build boost logic
        boost_cases = []
        
        if parsed['target_fields'] and parsed['entities']:
            entity_value = None
            if 'person_name' in parsed['entities']:
                entity_value = parsed['entities']['person_name']
            elif 'project_name' in parsed['entities']:
                entity_value = parsed['entities']['project_name']
            
            if entity_value:
                entity_escaped = entity_value.replace("'", "''")
                
                field_labels = {
                    'updatedby': 'Updated By',
                    'createdby': 'Created By',
                    'responsibleemployeename': 'Responsible Employee',
                    'contactfirstname': 'Contact First Name',
                    'contactlastname': 'Contact Last Name',
                    'projectname': 'Project',
                    'projectdesc': 'Description'
                }
                
                for field in parsed['target_fields']:
                    if field in field_labels:
                        label = field_labels[field]
                        boost_cases.append(f"WHEN e.text_chunk LIKE '%{label}: %{entity_escaped}%' THEN 2.0")
                
                boost_cases.append(f"WHEN e.text_chunk LIKE '%{entity_escaped}%' THEN 1.5")
        
        # Build boost SQL - FIX: Only add ELSE once
        if not boost_cases:
            boost_sql = "1.0 as boost"
            order_boost_sql = "1.0"
        else:
            boost_cases.append("ELSE 1.0")  # Add ELSE only once
            boost_sql = "CASE " + " ".join(boost_cases) + " END as boost"
            # For ORDER BY, need to repeat the CASE statement
            order_boost_sql = "CASE " + " ".join(boost_cases) + " END"
        
        # Build WHERE clause
        embedding_where = "WHERE e.embedding IS NOT NULL"
        
        join_sql = ""
        if request_filter_sql:
            join_sql = """
            INNER JOIN requests r ON e.requestid = r.requestid
        """
            embedding_where += " AND " + request_filter_sql.replace("WHERE ", "")
        
        # Execute search
        print("Searching database...")
        
        search_sql = f"""
            SELECT 
                e.requestid,
                e.chunk_index,
                LEFT(e.text_chunk, 250) as text_preview,
                1 - (e.embedding <=> t.embedding) as similarity,
                {boost_sql}
            FROM request_embeddings e
            {join_sql}
            CROSS JOIN temp_query_embedding t
            {embedding_where}
            ORDER BY (1 - (e.embedding <=> t.embedding)) * ({order_boost_sql}) DESC
            LIMIT 20;
        """
        
        if filter_params:
            cursor.execute(search_sql, tuple(filter_params))
        else:
            cursor.execute(search_sql)
        
        chunk_results = cursor.fetchall()
        
        print(f"✓ Found {len(chunk_results)} chunk results")
        print()
        
        if chunk_results:
            # Group by request ID
            request_scores = {}
            for req_id, chunk_idx, text_preview, similarity, boost in chunk_results:
                if req_id not in request_scores:
                    request_scores[req_id] = {
                        'best_similarity': similarity,
                        'best_chunk': chunk_idx,
                        'boost': float(boost) if boost else 1.0
                    }
                else:
                    if similarity > request_scores[req_id]['best_similarity']:
                        request_scores[req_id]['best_similarity'] = similarity
                        request_scores[req_id]['best_chunk'] = chunk_idx
            
            sorted_requests = sorted(
                request_scores.items(),
                key=lambda x: x[1]['best_similarity'] * x[1]['boost'],
                reverse=True
            )
            
            unique_request_ids = [req_id for req_id, _ in sorted_requests[:10]]
            
            print(f"✓ Found {len(unique_request_ids)} unique requests")
            print()
            print("Top 5 Results:")
            for i, (req_id, score_info) in enumerate(sorted_requests[:5], 1):
                similarity = score_info['best_similarity']
                boost = score_info['boost']
                print(f"  {i}. Request {req_id} - Similarity: {similarity:.4f} ({similarity*100:.2f}%), Boost: {boost:.2f}x")
            print()
        else:
            print("⚠ No results found")
            print()
        
        # Clean up
        cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Main test
if __name__ == "__main__":
    print("=" * 80)
    print("SEARCH TEST - Query Parser Integration")
    print("=" * 80)
    print()
    
    # Load config
    config_path = Path(__file__).parent.parent.parent / "config" / "search_config.json"
    config = None
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("✓ Loaded search configuration")
        except Exception as e:
            print(f"⚠ Could not load config: {e}, using defaults")
    else:
        print("⚠ Config file not found, using defaults")
    
    print()
    print(f"Testing {len(TEST_QUERIES)} queries...")
    print()
    
    results = []
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*80}\nTEST {i}/{len(TEST_QUERIES)}\n{'='*80}\n")
        success = run_search_test(query, config)
        results.append((query, success))
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    for query, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {fix_hebrew_rtl(query)}")
    print()
    
    passed = sum(1 for _, success in results if success)
    print(f"Results: {passed}/{len(results)} tests passed")
    print()

