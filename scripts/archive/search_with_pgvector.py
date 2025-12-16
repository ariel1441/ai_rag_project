"""
Vector search using pgvector Python package (proper vector support).
This should fix the 0 results issue!
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
print("Vector Search with pgvector Package")
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

# Get query
query = sys.argv[1] if len(sys.argv) > 1 else "אלינור"
print(f"Searching for: '{query}'")
print()

try:
    # Connect
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    
    # Register vector type (IMPORTANT!)
    register_vector(conn)
    
    cursor = conn.cursor()
    
    # Generate embedding
    print("Generating embedding...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    print(f"✓ Embedding generated: {len(query_embedding)} dimensions")
    print(f"  Type: {type(query_embedding)}")
    print()
    
    # Search using proper vector type (no string conversion!)
    print("Searching database...")
    search_query = """
        SELECT 
            requestid,
            chunk_index,
            LEFT(text_chunk, 200) as text_preview,
            1 - (embedding <=> %s) as similarity
        FROM request_embeddings
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s
        LIMIT 20;
    """
    
    # Pass numpy array directly (pgvector handles conversion)
    cursor.execute(search_query, (query_embedding, query_embedding))
    results = cursor.fetchall()
    
    print(f"✓ Found {len(results)} results")
    print()
    
    if results:
        print("=" * 70)
        print("TOP RESULTS")
        print("=" * 70)
        print()
        
        query_in_results = 0
        for i, (req_id, chunk_idx, text_preview, similarity) in enumerate(results, 1):
            has_query = query in text_preview
            if has_query:
                query_in_results += 1
            
            marker = "✓" if has_query else " "
            print(f"{i}. {marker} Request {req_id} (Chunk {chunk_idx})")
            print(f"   Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
            if has_query:
                print(f"   ✓ Contains '{query}'")
            print(f"   Text: {text_preview[:150]}")
            print()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total results: {len(results)}")
        print(f"Results containing '{query}': {query_in_results}/{len(results)}")
        print(f"Best similarity: {results[0][3]:.4f} ({results[0][3]*100:.2f}%)")
        
        if query_in_results > 0:
            print()
            print("✅ SUCCESS! Search is working with pgvector package!")
        else:
            print()
            print("⚠ Search works but top results don't contain exact query")
            print("  This is normal - semantic search finds similar meaning")
    else:
        print("❌ Still no results")
        print()
        print("Debugging:")
        cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
        total = cursor.fetchone()[0]
        print(f"  Total embeddings: {total}")
        
        cursor.execute(f"SELECT COUNT(*) FROM request_embeddings WHERE text_chunk LIKE '%{query}%';")
        text_count = cursor.fetchone()[0]
        print(f"  Embeddings with '{query}' in text: {text_count}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("If you see 'register_vector' error, make sure pgvector package is installed:")
    print("  python -m pip install pgvector")

print()
print("=" * 70)

