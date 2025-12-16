"""
Main search script - uses hybrid method (keyword + semantic) by default.
This is the recommended search script to use.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import os
import sys
import re

# Fix Hebrew RTL display - reverses Hebrew text for correct display in LTR terminals
def fix_hebrew_rtl(text):
    """
    Fix Hebrew RTL display for LTR terminals.
    Reverses Hebrew text segments so they display correctly.
    Data in database is CORRECT - this is display only.
    """
    if not text:
        return text
    
    # Hebrew Unicode range: \u0590-\u05FF
    # Split text into Hebrew and non-Hebrew segments
    pattern = r'([\u0590-\u05FF]+|[^\u0590-\u05FF]+)'
    parts = re.findall(pattern, str(text))
    
    result = []
    for part in parts:
        # If Hebrew text, reverse it for display
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

print("=" * 70)
print("Semantic Search (Hybrid: Keyword + Semantic)")
print("=" * 70)
print()
print("You can search with ANY query - it will find semantically similar requests!")
print("The hybrid method combines keyword filtering with semantic ranking")
print("for the best results.")
print()
print("Examples:")
print("  - 'אלינור'")
print("  - 'בנית בנין'")
print("  - 'פניות שקשורות למיילים'")
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

# Fix query display (for terminal - data is correct)
query_display = fix_hebrew_rtl(query)

print()
print(f"Searching for: '{query_display}'")
print()

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    register_vector(conn)
    cursor = conn.cursor()
    
    # Keyword detection for hybrid search
    email_keywords = ['מייל', 'email', 'mail', 'אימייל', 'תבנית מייל', 'מיילים']
    request_keywords = ['פניות', 'בקשות', 'request', 'פנייה']
    building_keywords = ['בניה', 'בנין', 'בנייה', 'building', 'construction']
    
    query_lower = query.lower()
    has_email_keyword = any(kw in query_lower for kw in email_keywords)
    has_building_keyword = any(kw in query_lower for kw in building_keywords)
    
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
    
    # HYBRID SEARCH: Keyword filter + Semantic ranking
    print("Searching database...")
    
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
    elif has_building_keyword:
        # Filter by building keywords
        keyword_filter = " OR ".join([f"e.text_chunk LIKE '%{kw}%'" for kw in building_keywords])
        
        cursor.execute(f"""
            SELECT 
                e.requestid,
                e.chunk_index,
                LEFT(e.text_chunk, 250) as text_preview,
                1 - (e.embedding <=> t.embedding) as similarity,
                1.0 as boost
            FROM request_embeddings e
            CROSS JOIN temp_query_embedding t
            WHERE e.embedding IS NOT NULL
              AND ({keyword_filter})
            ORDER BY e.embedding <=> t.embedding
            LIMIT 20;
        """)
    else:
        # Pure semantic search (no keyword filter)
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
        print("TOP RESULTS")
        print("=" * 70)
        print()
        
        for i, (req_id, chunk_idx, text_preview, similarity, boost) in enumerate(results, 1):
            # Convert boost to float
            boost_float = float(boost) if boost else 1.0
            adjusted_similarity = similarity * boost_float
            
            # Fix Hebrew RTL display (data is correct, just fix display)
            text_display = fix_hebrew_rtl(text_preview)
            
            print(f"{i}. Request {req_id} (Chunk {chunk_idx})")
            print(f"   Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
            if boost_float > 1.0:
                print(f"   Boosted: {adjusted_similarity:.4f} ({adjusted_similarity*100:.2f}%)")
            print(f"   Text: {text_display}")
            print()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total results: {len(results)}")
        print(f"Best similarity: {results[0][3]:.4f} ({results[0][3]*100:.2f}%)")
        print()
        print("Note: This is HYBRID search - combines keyword filtering")
        print("      with semantic ranking for best results.")
        print()
        print("Note: Hebrew text has been reversed for correct display.")
        print("      Data in database is CORRECT - this is display only.")
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

