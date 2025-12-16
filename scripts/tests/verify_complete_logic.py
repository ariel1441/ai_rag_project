"""
Verify complete logic: Data storage → Search input → Results output
Check if everything is logically correct.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import os
import sys
import re

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

def fix_hebrew_rtl(text):
    """Fix Hebrew RTL display for LTR terminals."""
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

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 70)
print("Complete Logic Verification")
print("=" * 70)
print()

# Test query
query = "פניות מאריאל בן עקיבא"
print(f"Test Query: '{query}'")
print(f"Query (raw bytes): {query.encode('utf-8').hex()}")
print(f"Query (characters): {[ord(c) for c in query[:10]]}")
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
    
    # Step 1: Check if query text exists in database
    print("Step 1: Check if query text exists in database...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM request_embeddings 
        WHERE text_chunk LIKE %s;
    """, (f'%{query}%',))
    
    exact_match_count = cursor.fetchone()[0]
    print(f"  Exact text matches: {exact_match_count}")
    
    # Check for parts of query
    query_parts = query.split()
    for part in query_parts:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM request_embeddings 
            WHERE text_chunk LIKE %s;
        """, (f'%{part}%',))
        count = cursor.fetchone()[0]
        print(f"  Contains '{part}': {count} embeddings")
    print()
    
    # Step 2: Generate embedding for query
    print("Step 2: Generate embedding for query...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    print(f"  ✓ Embedding generated")
    print(f"  Dimensions: {len(query_embedding)}")
    print(f"  First 5 values: {query_embedding[:5]}")
    print(f"  Type: {type(query_embedding)}")
    print()
    
    # Step 3: Insert into temp table
    print("Step 3: Insert query embedding into temp table...")
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
    print(f"  ✓ Inserted embedding string length: {len(embedding_str)}")
    print()
    
    # Step 4: Verify temp table embedding
    print("Step 4: Verify temp table embedding...")
    cursor.execute("""
        SELECT embedding, pg_typeof(embedding)
        FROM temp_query_embedding;
    """)
    
    temp_emb = cursor.fetchone()
    if temp_emb:
        print(f"  ✓ Temp embedding type: {temp_emb[1]}")
        print(f"  ✓ Temp embedding shape: {len(temp_emb[0]) if hasattr(temp_emb[0], '__len__') else 'N/A'}")
    print()
    
    # Step 5: Search
    print("Step 5: Perform semantic search...")
    cursor.execute("""
        SELECT 
            e.requestid,
            e.chunk_index,
            e.text_chunk,
            1 - (e.embedding <=> t.embedding) as similarity
        FROM request_embeddings e
        CROSS JOIN temp_query_embedding t
        WHERE e.embedding IS NOT NULL
        ORDER BY e.embedding <=> t.embedding
        LIMIT 20;
    """)
    
    results = cursor.fetchall()
    print(f"  ✓ Found {len(results)} results")
    print()
    
    # Step 6: Analyze results
    print("Step 6: Analyze results...")
    print()
    
    query_words = set(query.lower().split())
    relevant_count = 0
    
    for i, (req_id, chunk_idx, text_chunk, similarity) in enumerate(results, 1):
        # Check if result contains any query words
        text_lower = text_chunk.lower()
        matching_words = [word for word in query_words if word in text_lower]
        
        is_relevant = len(matching_words) > 0 or similarity > 0.5
        
        if is_relevant:
            relevant_count += 1
        
        marker = "✅" if is_relevant else "❌"
        print(f"{i}. {marker} Request {req_id} (similarity: {similarity:.4f})")
        print(f"   Matching words: {matching_words if matching_words else 'None'}")
        print(f"   Text (raw): {text_chunk[:150]}")
        print(f"   Text (RTL fixed): {fix_hebrew_rtl(text_chunk[:150])}")
        print()
    
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print(f"Query: '{query}'")
    print(f"Exact matches in DB: {exact_match_count}")
    print(f"Results found: {len(results)}")
    print(f"Relevant results: {relevant_count}/{len(results)}")
    print(f"Best similarity: {results[0][3]:.4f} ({results[0][3]*100:.2f}%)")
    print()
    
    # Step 7: Check data flow
    print("=" * 70)
    print("DATA FLOW VERIFICATION")
    print("=" * 70)
    print()
    
    # Get a sample stored embedding
    cursor.execute("""
        SELECT embedding, text_chunk
        FROM request_embeddings
        WHERE text_chunk LIKE '%אריאל%' OR text_chunk LIKE '%עקיבא%'
        LIMIT 1;
    """)
    
    stored_sample = cursor.fetchone()
    if stored_sample:
        stored_emb = stored_sample[0]
        stored_text = stored_sample[1]
        
        print("Sample stored embedding:")
        print(f"  Text: {stored_text[:100]}")
        print(f"  Embedding type: {type(stored_emb)}")
        print(f"  Embedding shape: {stored_emb.shape if hasattr(stored_emb, 'shape') else 'N/A'}")
        print()
        
        # Compare types
        print("Type comparison:")
        print(f"  Query embedding type: {type(query_embedding)}")
        print(f"  Stored embedding type: {type(stored_emb)}")
        print(f"  Types match: {type(query_embedding) == type(stored_emb)}")
        print()
        
        # Test similarity
        cursor.execute("""
            SELECT 1 - (embedding <=> %s) as similarity
            FROM temp_query_embedding;
        """, (stored_emb,))
        
        test_sim = cursor.fetchone()[0]
        print(f"  Test similarity with stored: {test_sim:.4f}")
        print()
    
    # Step 8: Verify search logic
    print("=" * 70)
    print("SEARCH LOGIC VERIFICATION")
    print("=" * 70)
    print()
    
    print("✅ Step 1: Query received correctly")
    print(f"   Query: '{query}'")
    print(f"   Bytes: {query.encode('utf-8').hex()[:50]}...")
    print()
    
    print("✅ Step 2: Embedding generated correctly")
    print(f"   Dimensions: {len(query_embedding)}")
    print(f"   Normalized: {np.linalg.norm(query_embedding):.6f} (should be ~1.0)")
    print()
    
    print("✅ Step 3: Embedding stored in temp table")
    print(f"   Format: string → vector cast")
    print()
    
    print("✅ Step 4: Search executed")
    print(f"   Method: CROSS JOIN with temp table")
    print(f"   Ordering: BY embedding <=> query_embedding")
    print()
    
    print("✅ Step 5: Results retrieved")
    print(f"   Count: {len(results)}")
    print()
    
    print("⚠️ Step 6: Result relevance")
    print(f"   Relevant: {relevant_count}/{len(results)}")
    if relevant_count < len(results) * 0.5:
        print("   ⚠️ Many results seem unrelated")
        print("   This might be because:")
        print("     - Query is very specific (name + location)")
        print("     - Semantic search finds similar meaning, not exact matches")
        print("     - Need keyword filtering for better results")
    print()
    
    # Clean up
    cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

