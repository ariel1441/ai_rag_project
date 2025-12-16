"""
Fixed search - uses exact same format as stored embeddings.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
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
print("Fixed Vector Search")
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
    cursor = conn.cursor()
    
    # Get stored embedding format to match
    print("Getting stored embedding format reference...")
    cursor.execute("""
        SELECT embedding::text
        FROM request_embeddings 
        LIMIT 1;
    """)
    stored_format = cursor.fetchone()[0]
    
    # Check format: count decimals, check precision
    # Stored format example: [-0.11389176,0.115577094,...]
    # We need to match this exact format
    
    # Generate query embedding
    print("Generating embedding...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    # Format to match stored format exactly
    # Stored uses: map(str, embedding) which gives full precision
    # But PostgreSQL may store with different precision
    # Let's try matching the stored format exactly
    
    # Method 1: Use same format as insertion (map(str, ...))
    embedding_list = query_embedding.tolist()
    embedding_str = '[' + ','.join(map(str, embedding_list)) + ']'
    
    print(f"✓ Embedding generated: {len(query_embedding)} dimensions")
    print(f"  Format length: {len(embedding_str)}")
    print()
    
    # Try search
    print("Searching database...")
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
            print("✅ SUCCESS! Search is working!")
        else:
            print()
            print("⚠ Search works but top results don't contain exact query")
            print("  This is normal - semantic search finds similar meaning")
    else:
        print("❌ Still no results")
        print()
        print("Trying alternative: Use stored embedding as query...")
        
        # Alternative: Use a stored embedding that contains the query text
        cursor.execute("""
            SELECT embedding::text
            FROM request_embeddings 
            WHERE text_chunk LIKE %s
            LIMIT 1;
        """, (f'%{query}%',))
        
        stored_emb = cursor.fetchone()
        if stored_emb:
            print("Using stored embedding for search...")
            cursor.execute(f"""
                SELECT 
                    requestid,
                    chunk_index,
                    LEFT(text_chunk, 200) as text_preview,
                    1 - (embedding <=> '{stored_emb[0]}'::vector) as similarity
                FROM request_embeddings
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> '{stored_emb[0]}'::vector
                LIMIT 10;
            """)
            
            alt_results = cursor.fetchall()
            if alt_results:
                print(f"✅ Alternative search found {len(alt_results)} results!")
                print("This confirms the issue is with query embedding format.")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

