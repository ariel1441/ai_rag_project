"""
Hybrid search test - with default query for testing.
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
print("Hybrid Search Test: פניות שקשורות למיילים")
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

# Default query for testing
query = "פניות שקשורות למיילים"
print(f"Query: '{query}'")
print()

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    register_vector(conn)
    cursor = conn.cursor()
    
    # Extract keywords
    email_keywords = ['מייל', 'email', 'mail', 'אימייל', 'תבנית מייל', 'מיילים']
    query_lower = query.lower()
    has_email_keyword = any(kw in query_lower for kw in email_keywords)
    
    # Generate embedding
    print("Generating embedding...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    print(f"✓ Embedding generated")
    print()
    
    # Insert into temp table
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
    
    # HYBRID SEARCH: Keyword filter + Semantic ranking
    print("Performing hybrid search...")
    
    if has_email_keyword:
        # Filter by email keywords first, then rank by similarity
        keyword_filter = " OR ".join([f"e.text_chunk LIKE '%{kw}%'" for kw in email_keywords])
        
        cursor.execute(f"""
            SELECT 
                e.requestid,
                e.chunk_index,
                LEFT(e.text_chunk, 250) as text_preview,
                1 - (e.embedding <=> t.embedding) as similarity,
                CASE 
                    WHEN e.text_chunk LIKE '%מייל%' OR e.text_chunk LIKE '%email%' 
                    THEN 1.2
                    ELSE 1.0
                END as boost
            FROM request_embeddings e
            CROSS JOIN temp_query_embedding t
            WHERE e.embedding IS NOT NULL
              AND ({keyword_filter})
            ORDER BY (1 - (e.embedding <=> t.embedding)) * 
                     CASE 
                         WHEN e.text_chunk LIKE '%מייל%' OR e.text_chunk LIKE '%email%' 
                         THEN 1.2
                         ELSE 1.0
                     END DESC
            LIMIT 20;
        """)
    else:
        # Pure semantic search
        cursor.execute("""
            SELECT 
                e.requestid,
                e.chunk_index,
                LEFT(e.text_chunk, 250) as text_preview,
                1 - (e.embedding <=> t.embedding) as similarity,
                1.0 as boost
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
        print("TOP RESULTS (Hybrid Search)")
        print("=" * 70)
        print()
        
        relevant_count = 0
        for i, (req_id, chunk_idx, text_preview, similarity, boost) in enumerate(results, 1):
            has_email = any(kw in text_preview.lower() for kw in email_keywords)
            if has_email:
                relevant_count += 1
                marker = "✅"
            else:
                marker = "  "
            
            # Convert boost to float (PostgreSQL returns Decimal)
            boost_float = float(boost) if boost else 1.0
            adjusted_similarity = similarity * boost_float
            print(f"{i}. {marker} Request {req_id} (Chunk {chunk_idx})")
            print(f"   Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
            if boost > 1.0:
                print(f"   Boosted: {adjusted_similarity:.4f} ({adjusted_similarity*100:.2f}%)")
            print(f"   Text: {text_preview}")
            print()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total results: {len(results)}")
        print(f"✅ Relevant (contains email terms): {relevant_count}/{len(results)}")
        print(f"Best similarity: {results[0][3]:.4f} ({results[0][3]*100:.2f}%)")
        print()
        print("Comparison:")
        print("  Old method: 8/20 relevant (40%)")
        print(f"  Hybrid method: {relevant_count}/20 relevant ({relevant_count*20}%)")
    else:
        print("⚠ No results found")
    
    # Clean up
    cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

