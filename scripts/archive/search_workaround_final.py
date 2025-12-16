"""
Working search - uses stored embedding as query (workaround).
This works while we debug the query embedding issue.
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
print("Vector Search (Workaround - Uses Stored Embedding)")
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
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    register_vector(conn)
    cursor = conn.cursor()
    
    # Strategy: Find a stored embedding that contains the query text
    # Then use that embedding to find similar ones
    print("Finding stored embedding with query text...")
    cursor.execute("""
        SELECT embedding, requestid, text_chunk
        FROM request_embeddings 
        WHERE text_chunk LIKE %s
        ORDER BY LENGTH(text_chunk) ASC
        LIMIT 1;
    """, (f'%{query}%',))
    
    stored_result = cursor.fetchone()
    
    if not stored_result:
        print(f"❌ No embeddings found containing '{query}'")
        print("   Try a different query or check spelling")
        conn.close()
        exit(1)
    
    stored_embedding = stored_result[0]
    source_request_id = stored_result[1]
    source_text = stored_result[2]
    
    print(f"✓ Found source embedding")
    print(f"  Request ID: {source_request_id}")
    print(f"  Text: {source_text[:150]}")
    print()
    
    # Now search using this stored embedding
    print("Searching for similar requests...")
    cursor.execute("""
        SELECT 
            requestid,
            chunk_index,
            LEFT(text_chunk, 200) as text_preview,
            1 - (embedding <=> %s) as similarity
        FROM request_embeddings
        WHERE embedding IS NOT NULL
          AND requestid != %s  -- Exclude the source request
        ORDER BY embedding <=> %s
        LIMIT 20;
    """, (stored_embedding, str(source_request_id), stored_embedding))
    
    results = cursor.fetchall()
    
    print(f"✓ Found {len(results)} similar requests")
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
        print(f"Source request: {source_request_id}")
        print(f"Total similar requests: {len(results)}")
        print(f"Results containing '{query}': {query_in_results}/{len(results)}")
        print(f"Best similarity: {results[0][3]:.4f} ({results[0][3]*100:.2f}%)")
        print()
        print("✅ Search working! (Using workaround method)")
        print()
        print("Note: This uses a stored embedding as the query.")
        print("      For new queries not in database, we need to fix the")
        print("      query embedding format issue.")
    else:
        print("⚠ No similar requests found")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

