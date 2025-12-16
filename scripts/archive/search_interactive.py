"""
Interactive search - test with any query you want!
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import os
import sys

# Fix Hebrew display
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        else:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 70)
print("Interactive Semantic Search")
print("=" * 70)
print()
print("You can search with ANY query - it will find semantically similar requests!")
print("Examples:")
print("  - 'אלינור'")
print("  - 'בנית בנין'")
print("  - 'תביא לי את כל הפניות שקשורות לבניה'")
print("  - 'בקשות מסוג 4'")
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

# Get query from user
query = input("Enter your search query: ").strip()
if not query:
    print("No query provided. Exiting.")
    exit(0)

print()
print(f"Searching for: '{query}'")
print()

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    register_vector(conn)
    cursor = conn.cursor()
    
    # Generate query embedding
    print("Generating embedding...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    print(f"✓ Embedding generated: {len(query_embedding)} dimensions")
    print()
    
    # Insert query embedding into temp table (the fix!)
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
    
    # Search
    print("Searching database...")
    cursor.execute("""
        SELECT 
            e.requestid,
            e.chunk_index,
            LEFT(e.text_chunk, 250) as text_preview,
            1 - (e.embedding <=> t.embedding) as similarity
        FROM request_embeddings e
        CROSS JOIN temp_query_embedding t
        WHERE e.embedding IS NOT NULL
        ORDER BY e.embedding <=> t.embedding
        LIMIT 20;
    """)
    
    results = cursor.fetchall()
    
    print(f"✓ Found {len(results)} results")
    print()
    
    if results:
        print("=" * 70)
        print("TOP RESULTS")
        print("=" * 70)
        print()
        
        for i, (req_id, chunk_idx, text_preview, similarity) in enumerate(results, 1):
            similarity_pct = similarity * 100
            print(f"{i}. Request {req_id} (Chunk {chunk_idx})")
            print(f"   Similarity: {similarity:.4f} ({similarity_pct:.2f}%)")
            print(f"   Text: {text_preview}")
            print()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total results: {len(results)}")
        print(f"Best similarity: {results[0][3]:.4f} ({results[0][3]*100:.2f}%)")
        print()
        print("Note: This is SEMANTIC search - it finds requests with similar")
        print("      meaning, not just exact text matches.")
    else:
        print("⚠ No results found")
        print()
        print("This might mean:")
        print("  - No requests are semantically similar to your query")
        print("  - Try a different query or more specific terms")
    
    # Clean up
    cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

