"""
Analyze search results - check relevance and explain logic.
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

# Query
query = "פניות שקשורות למיילים"
print("=" * 70)
print("Search Analysis: פניות שקשורות למיילים")
print("=" * 70)
print()
print("Query meaning: 'Requests related to emails'")
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
    
    # Generate query embedding
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
    
    # Search
    print("Searching database...")
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
    
    print(f"✓ Found {len(results)} results")
    print()
    
    # Analyze results
    print("=" * 70)
    print("DETAILED ANALYSIS")
    print("=" * 70)
    print()
    
    # Keywords to look for
    email_keywords = ['מייל', 'email', 'mail', 'אימייל', 'תבנית מייל', 'מיילים']
    request_keywords = ['פניות', 'בקשות', 'request', 'פנייה']
    
    relevant_count = 0
    partially_relevant = 0
    not_relevant = 0
    
    for i, (req_id, chunk_idx, text_chunk, similarity) in enumerate(results, 1):
        # Check if contains email-related terms
        has_email = any(keyword in text_chunk.lower() for keyword in email_keywords)
        has_request = any(keyword in text_chunk.lower() for keyword in request_keywords)
        
        # Determine relevance
        if has_email:
            relevant_count += 1
            relevance = "✅ RELEVANT"
        elif has_request and similarity > 0.5:
            partially_relevant += 1
            relevance = "⚠️ PARTIALLY RELEVANT"
        else:
            not_relevant += 1
            relevance = "❌ NOT RELEVANT"
        
        print(f"{i}. {relevance} - Request {req_id}")
        print(f"   Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
        print(f"   Contains 'מייל/email': {has_email}")
        print(f"   Contains 'פניות/request': {has_request}")
        print(f"   Text: {text_chunk[:200]}")
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total results: {len(results)}")
    print(f"✅ Relevant (contains email-related terms): {relevant_count}")
    print(f"⚠️ Partially relevant (requests but no email): {partially_relevant}")
    print(f"❌ Not relevant: {not_relevant}")
    print()
    
    # Check what might be missing
    print("Checking for requests that might be missing...")
    cursor.execute("""
        SELECT requestid, text_chunk
        FROM request_embeddings
        WHERE text_chunk LIKE '%מייל%'
           OR text_chunk LIKE '%email%'
           OR text_chunk LIKE '%mail%'
           OR text_chunk LIKE '%אימייל%'
           OR text_chunk LIKE '%תבנית מייל%'
        ORDER BY requestid
        LIMIT 50;
    """)
    
    all_email_requests = cursor.fetchall()
    found_ids = {r[0] for r in results}
    
    missing = [r for r in all_email_requests if r[0] not in found_ids]
    
    if missing:
        print(f"⚠️ Found {len(missing)} requests with email-related terms NOT in top 20:")
        for req_id, text in missing[:10]:
            print(f"  - Request {req_id}: {text[:150]}")
    else:
        print("✅ All email-related requests are in top 20!")
    
    print()
    
    # Explain logic
    print("=" * 70)
    print("HOW SEMANTIC SEARCH WORKS")
    print("=" * 70)
    print()
    print("1. Query: 'פניות שקשורות למיילים'")
    print("   Meaning: 'Requests related to emails'")
    print()
    print("2. Embedding model converts to numbers representing meaning:")
    print("   - 'פניות' (requests) → certain numbers")
    print("   - 'מיילים' (emails) → certain numbers")
    print("   - Combined meaning → 384 numbers")
    print()
    print("3. System compares with all stored embeddings:")
    print("   - Calculates similarity (how close the meanings are)")
    print("   - Returns top 20 most similar")
    print()
    print("4. Why some results might seem unrelated:")
    print("   - Semantic search finds MEANING, not exact words")
    print("   - 'פניות' (requests) might match other request-related text")
    print("   - If request text is similar in meaning, it appears")
    print("   - Lower similarity = less related")
    print()
    print("5. Why result #3 might not look related:")
    print("   - It has high similarity score (meaning is close)")
    print("   - But might not contain exact keywords")
    print("   - Semantic search prioritizes MEANING over KEYWORDS")
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

