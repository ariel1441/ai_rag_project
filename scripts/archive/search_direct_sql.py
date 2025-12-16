"""
Direct SQL search - matches how embeddings were inserted.
This should work!
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import sys

# Fix encoding
if sys.platform == 'win32':
    try:
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
print("Direct SQL Vector Search")
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
import sys
query = sys.argv[1] if len(sys.argv) > 1 else "אלינור"
print(f"Searching for: '{query}'")
print()

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    cursor = conn.cursor()
    
    # Generate embedding (same as insertion)
    print("Generating embedding...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    # Format EXACTLY like insertion: '[0.1,0.2,0.3,...]'
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    print(f"✓ Embedding: {len(query_embedding)} dimensions")
    print()
    
    # Direct SQL (no parameterization) - matches insertion method
    print("Executing search query...")
    search_sql = f"""
        SELECT 
            requestid,
            chunk_index,
            LEFT(text_chunk, 200) as text_preview,
            1 - (embedding <=> '{embedding_str}'::vector) as similarity
        FROM request_embeddings
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT 20;
    """
    
    cursor.execute(search_sql)
    results = cursor.fetchall()
    
    print(f"✓ Query executed")
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
            print(f"   Text: {text_preview}")
            print()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total results: {len(results)}")
        print(f"Results containing '{query}': {query_in_results}/{len(results)}")
        print(f"Best similarity: {results[0][3]:.4f} ({results[0][3]*100:.2f}%)")
        
        if query_in_results > 0:
            print()
            print("✅ SUCCESS! Search is working!")
        else:
            print()
            print("⚠ Search works but top results don't contain exact query")
            print("  This is normal - semantic search finds similar meaning")
    else:
        print("❌ No results found")
        print()
        print("Debugging info:")
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
print("=" * 70)

