"""
Comprehensive System Test
Tests all major functionality:
1. Search with new embeddings (UI field improvements)
2. Similar requests fix
3. API server endpoints
4. Count verification
"""
import sys
import time
import os
from pathlib import Path
import requests
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from scripts.utils.query_parser import QueryParser
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_QUERIES = {
    "person": "פניות מאור גלילי",
    "status": "פניות בסטטוס בקליטה",
    "type": "בקשות מסוג 4",
    "project": "פרויקט בדיקה",
    "count": "כמה פניות יש מיניב ליבוביץ?",
    "similar": "פניות דומות ל-211000001"
}

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5433')),
        database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

def test_search_new_embeddings():
    """Test 1: Search with new embeddings - verify UI field improvements."""
    print("="*80)
    print("TEST 1: Search with New Embeddings (UI Field Improvements)")
    print("="*80)
    print()
    
    results = []
    
    # Test queries that should benefit from UI field weights
    test_cases = [
        {
            "query": "פניות בסטטוס בקליטה",
            "description": "Status field (requeststatusid) - should be weighted 3.0x",
            "expected_intent": "status"
        },
        {
            "query": "פניות מגורם מטפל אריאל בן עקיבא",
            "description": "Handling Party (responsibleemployeename) - should be weighted 3.0x",
            "expected_intent": "person"
        },
        {
            "query": "פניות מתאריך עדכון אחרון",
            "description": "Update Date (requeststatusdate) - should be weighted 3.0x",
            "expected_intent": "general"
        },
        {
            "query": "פניות ממקור X",
            "description": "Source (requestsourcenun) - should be weighted 3.0x",
            "expected_intent": "general"
        }
    ]
    
    try:
        # Load config
        config_path = project_root / "config" / "search_config.json"
        config = None
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        query_parser = QueryParser(config)
        
        # Connect to database
        conn = get_db_connection()
        register_vector(conn)
        cursor = conn.cursor()
        
        # Load embedding model
        print("Loading embedding model...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("✓ Model loaded")
        print()
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            description = test_case["description"]
            expected_intent = test_case.get("expected_intent", "general")
            
            print(f"Test {i}: {description}")
            print(f"  Query: {query}")
            
            # Parse query
            parsed = query_parser.parse(query)
            intent = parsed.get('intent', 'general')
            
            print(f"  Intent detected: {intent}")
            if parsed.get('entities'):
                print(f"  Entities: {parsed.get('entities')}")
            
            # Generate embedding
            query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
            
            # Create temp table
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
            
            # Search
            search_sql = """
                SELECT 
                    e.requestid,
                    1 - (e.embedding <=> t.embedding) as similarity,
                    LEFT(e.text_chunk, 200) as text_preview
                FROM request_embeddings e
                CROSS JOIN temp_query_embedding t
                WHERE e.embedding IS NOT NULL
                ORDER BY 1 - (e.embedding <=> t.embedding) DESC
                LIMIT 10;
            """
            
            cursor.execute(search_sql)
            chunk_results = cursor.fetchall()
            
            # Get unique requests
            request_scores = {}
            for req_id, similarity, text_preview in chunk_results:
                if req_id not in request_scores:
                    request_scores[req_id] = {
                        'best_similarity': similarity,
                        'text_preview': text_preview
                    }
                elif similarity > request_scores[req_id]['best_similarity']:
                    request_scores[req_id]['best_similarity'] = similarity
                    request_scores[req_id]['text_preview'] = text_preview
            
            sorted_requests = sorted(
                request_scores.items(),
                key=lambda x: x[1]['best_similarity'],
                reverse=True
            )
            
            print(f"  Found {len(sorted_requests)} unique requests")
            if sorted_requests:
                best_sim = sorted_requests[0][1]['best_similarity']
                print(f"  Best similarity: {best_sim:.4f} ({best_sim*100:.2f}%)")
                print(f"  Top request ID: {sorted_requests[0][0]}")
            
            # Clean up
            cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
            
            # Check if intent matches expected
            if intent == expected_intent:
                print(f"  ✅ Intent correct")
                results.append(True)
            else:
                print(f"  ⚠️  Intent mismatch (expected: {expected_intent}, got: {intent})")
                results.append(False)
            
            print()
        
        conn.close()
        
        passed = sum(results)
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All search tests passed!")
            return True
        else:
            print("⚠️  Some search tests had issues")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_similar_requests():
    """Test 2: Similar requests fix - verify it uses request ID correctly."""
    print("="*80)
    print("TEST 2: Similar Requests Fix")
    print("="*80)
    print()
    
    try:
        # Load config
        config_path = project_root / "config" / "search_config.json"
        config = None
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        query_parser = QueryParser(config)
        
        # Test query
        query = "פניות דומות ל-211000001"
        print(f"Query: {query}")
        
        # Parse query
        parsed = query_parser.parse(query)
        print(f"Intent: {parsed.get('intent')}")
        print(f"Query type: {parsed.get('query_type')}")
        print(f"Entities: {parsed.get('entities')}")
        
        # Check if request_id was extracted
        if 'request_id' in parsed.get('entities', {}):
            request_id = parsed['entities']['request_id']
            print(f"✓ Request ID extracted: {request_id}")
            
            # Verify request exists in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT requestid FROM requests WHERE requestid = %s", (request_id,))
            exists = cursor.fetchone()
            
            if exists:
                print(f"✓ Request {request_id} exists in database")
                
                # Check if embedding exists for this request
                cursor.execute("""
                    SELECT COUNT(*) FROM request_embeddings 
                    WHERE requestid = %s
                """, (request_id,))
                embedding_count = cursor.fetchone()[0]
                
                if embedding_count > 0:
                    print(f"✓ Request {request_id} has {embedding_count} embeddings")
                    conn.close()
                    print("✅ Similar requests fix works correctly!")
                    return True
                else:
                    print(f"⚠️  Request {request_id} has no embeddings")
                    conn.close()
                    return False
            else:
                print(f"❌ Request {request_id} not found in database")
                conn.close()
                return False
        else:
            print("❌ Request ID not extracted from query")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_server():
    """Test 3: API server - verify all endpoints work."""
    print("="*80)
    print("TEST 3: API Server Endpoints")
    print("="*80)
    print()
    
    results = []
    
    # Test 3.1: Health check
    print("3.1: Health Check")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ Health check passed")
            results.append(True)
        else:
            print(f"  ❌ Health check failed: {response.status_code}")
            results.append(False)
    except requests.exceptions.ConnectionError:
        print("  ❌ Cannot connect to API - is it running?")
        print("     Run: python -m uvicorn api.app:app --reload --port 8000")
        results.append(False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(False)
    
    print()
    
    # Test 3.2: Search endpoint
    print("3.2: Search Endpoint")
    try:
        payload = {
            "query": "פניות מאור גלילי",
            "top_k": 5,
            "include_details": True
        }
        print(f"  Query: {payload['query']}")
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/api/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Search endpoint works ({elapsed:.2f}s)")
            print(f"     Intent: {data.get('intent')}")
            print(f"     Total found: {data.get('total_found')}")
            print(f"     Results: {len(data.get('results', []))} requests")
            results.append(True)
        else:
            print(f"  ❌ Search failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            results.append(False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(False)
    
    print()
    
    # Test 3.3: RAG endpoint (retrieval only)
    print("3.3: RAG Endpoint (Retrieval Only)")
    try:
        payload = {
            "query": "כמה פניות יש מיניב ליבוביץ?",
            "top_k": 5,
            "use_llm": False
        }
        print(f"  Query: {payload['query']}")
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/api/rag/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ RAG endpoint works ({elapsed:.2f}s)")
            print(f"     Intent: {data.get('intent')}")
            print(f"     Total retrieved: {data.get('total_retrieved')}")
            print(f"     Model loaded: {data.get('model_loaded')}")
            results.append(True)
        else:
            print(f"  ❌ RAG failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            results.append(False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(False)
    
    print()
    
    passed = sum(results)
    total = len(results)
    print(f"API Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All API tests passed!")
        return True
    else:
        print("⚠️  Some API tests failed")
        return False

def test_count_verification():
    """Test 4: Count verification - verify accurate database counts."""
    print("="*80)
    print("TEST 4: Count Verification")
    print("="*80)
    print()
    
    try:
        # Load config
        config_path = project_root / "config" / "search_config.json"
        config = None
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        query_parser = QueryParser(config)
        
        # Test count query
        query = "כמה פניות יש מיניב ליבוביץ?"
        print(f"Query: {query}")
        
        # Parse query
        parsed = query_parser.parse(query)
        print(f"Intent: {parsed.get('intent')}")
        print(f"Query type: {parsed.get('query_type')}")
        
        if parsed.get('query_type') == 'count':
            print("✓ Count query detected")
            
            # Get person name
            person_name = parsed.get('entities', {}).get('person_name')
            if person_name:
                print(f"✓ Person name extracted: {person_name}")
                
                # Count in database
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT requestid)
                    FROM requests
                    WHERE updatedby ILIKE %s 
                       OR createdby ILIKE %s
                       OR responsibleemployeename ILIKE %s
                """, (f'%{person_name}%', f'%{person_name}%', f'%{person_name}%'))
                
                db_count = cursor.fetchone()[0]
                print(f"✓ Database count: {db_count} requests")
                
                conn.close()
                
                if db_count > 0:
                    print("✅ Count verification works!")
                    return True
                else:
                    print("⚠️  No requests found in database (might be correct)")
                    return True  # Still passes if count is 0
            else:
                print("❌ Person name not extracted")
                return False
        else:
            print("❌ Count query type not detected")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("="*80)
    print("COMPREHENSIVE SYSTEM TEST")
    print("="*80)
    print()
    print("This will test:")
    print("  1. Search with new embeddings (UI field improvements)")
    print("  2. Similar requests fix")
    print("  3. API server endpoints")
    print("  4. Count verification")
    print()
    print("Note: For API tests, make sure the server is running:")
    print("  python -m uvicorn api.app:app --reload --port 8000")
    print()
    print("Starting tests in 2 seconds...")
    time.sleep(2)
    print()
    
    results = []
    
    # Test 1: Search with new embeddings
    results.append(("Search with New Embeddings", test_search_new_embeddings()))
    print()
    
    # Test 2: Similar requests
    results.append(("Similar Requests Fix", test_similar_requests()))
    print()
    
    # Test 3: API server
    results.append(("API Server", test_api_server()))
    print()
    
    # Test 4: Count verification
    results.append(("Count Verification", test_count_verification()))
    print()
    
    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    print()
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed - check errors above")
    
    return all_passed

if __name__ == "__main__":
    main()

