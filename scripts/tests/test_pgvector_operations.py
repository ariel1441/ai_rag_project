"""
Test pgvector operations to understand the issue.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import os
import sys

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 70)
print("Test pgvector Operations")
print("=" * 70)
print()

# Connection
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5433")
database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD")

if not password:
    print("ERROR: POSTGRES_PASSWORD not in .env!")
    exit(1)

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    register_vector(conn)
    cursor = conn.cursor()
    
    # Test 1: Get a stored embedding
    print("Test 1: Get stored embedding...")
    cursor.execute("""
        SELECT embedding, text_chunk
        FROM request_embeddings 
        WHERE text_chunk LIKE '%אלינור%'
        LIMIT 1;
    """)
    
    stored_result = cursor.fetchone()
    if not stored_result:
        print("❌ No embeddings found")
        exit(1)
    
    stored_embedding = stored_result[0]
    stored_text = stored_result[1]
    
    print(f"✓ Found embedding")
    print(f"  Type: {type(stored_embedding)}")
    print(f"  Shape: {stored_embedding.shape if hasattr(stored_embedding, 'shape') else 'N/A'}")
    print(f"  Text: {stored_text[:100]}")
    print()
    
    # Test 2: Self-similarity (should be 1.0)
    print("Test 2: Self-similarity...")
    # Use the same embedding we just retrieved
    cursor.execute("""
        SELECT 1 - (embedding <=> embedding) as similarity
        FROM request_embeddings 
        WHERE text_chunk LIKE '%אלינור%'
        LIMIT 1;
    """)
    
    self_sim = cursor.fetchone()[0]
    print(f"  Self-similarity: {self_sim:.6f} (should be 1.0)")
    if abs(self_sim - 1.0) < 0.0001:
        print("  ✓ Self-similarity works!")
    else:
        print("  ⚠ Self-similarity not exactly 1.0")
    print()
    
    # Test 3: Generate query embedding
    print("Test 3: Generate query embedding...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query = "אלינור"
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    print(f"  Query embedding type: {type(query_embedding)}")
    print(f"  Query embedding shape: {query_embedding.shape}")
    print(f"  Stored embedding type: {type(stored_embedding)}")
    print()
    
    # Test 4: Compare types
    print("Test 4: Compare embedding types...")
    if type(stored_embedding) == type(query_embedding):
        print("  ✓ Types match")
    else:
        print(f"  ⚠ Types differ: {type(stored_embedding)} vs {type(query_embedding)}")
    
    if hasattr(stored_embedding, 'shape') and hasattr(query_embedding, 'shape'):
        if stored_embedding.shape == query_embedding.shape:
            print("  ✓ Shapes match")
        else:
            print(f"  ⚠ Shapes differ: {stored_embedding.shape} vs {query_embedding.shape}")
    print()
    
    # Test 5: Try search with query embedding
    print("Test 5: Search with query embedding...")
    cursor.execute("""
        SELECT 
            requestid,
            text_chunk,
            1 - (embedding <=> %s) as similarity
        FROM request_embeddings
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s
        LIMIT 5;
    """, (query_embedding, query_embedding))
    
    query_results = cursor.fetchall()
    print(f"  Results: {len(query_results)}")
    
    if query_results:
        print("  ✓ Search works!")
        for i, (req_id, text, sim) in enumerate(query_results[:3], 1):
            print(f"    {i}. Request {req_id}: {sim:.4f}")
    else:
        print("  ❌ No results")
    print()
    
    # Test 6: Try search with stored embedding
    print("Test 6: Search with stored embedding...")
    cursor.execute("""
        SELECT 
            requestid,
            text_chunk,
            1 - (embedding <=> %s) as similarity
        FROM request_embeddings
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s
        LIMIT 5;
    """, (stored_embedding, stored_embedding))
    
    stored_results = cursor.fetchall()
    print(f"  Results: {len(stored_results)}")
    
    if stored_results:
        print("  ✓ Search works!")
        for i, (req_id, text, sim) in enumerate(stored_results[:3], 1):
            print(f"    {i}. Request {req_id}: {sim:.4f}")
    else:
        print("  ❌ No results")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Self-similarity: {self_sim:.6f}")
    print(f"Query search results: {len(query_results)}")
    print(f"Stored search results: {len(stored_results)}")
    
    if len(query_results) == 0 and len(stored_results) > 0:
        print()
        print("🔴 ISSUE: Query embedding search fails, but stored embedding search works")
        print("   This suggests the query embedding format/type is the problem")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

