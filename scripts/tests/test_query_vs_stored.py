"""
Compare query embedding format with stored embedding format.
This will help us understand why search fails.
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
print("Compare Query Embedding vs Stored Embedding Format")
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
    cursor = conn.cursor()
    
    # Get a stored embedding
    print("Step 1: Get stored embedding from database...")
    cursor.execute("""
        SELECT embedding::text, text_chunk
        FROM request_embeddings 
        WHERE text_chunk LIKE '%אלינור%'
        LIMIT 1;
    """)
    
    stored_result = cursor.fetchone()
    if not stored_result:
        print("❌ No embeddings found with 'אלינור'")
        exit(1)
    
    stored_embedding_str = stored_result[0]
    stored_text = stored_result[1]
    
    print(f"✓ Found stored embedding")
    print(f"  Text: {stored_text[:100]}")
    print(f"  Format length: {len(stored_embedding_str)}")
    print(f"  First 100 chars: {stored_embedding_str[:100]}")
    print()
    
    # Generate query embedding
    print("Step 2: Generate query embedding...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query = "אלינור"
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    # Format like we do for search
    query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    print(f"✓ Generated query embedding")
    print(f"  Dimensions: {len(query_embedding)}")
    print(f"  Format length: {len(query_embedding_str)}")
    print(f"  First 100 chars: {query_embedding_str[:100]}")
    print()
    
    # Compare formats
    print("Step 3: Compare formats...")
    print("-" * 70)
    
    # Check if lengths match
    if len(stored_embedding_str) == len(query_embedding_str):
        print("✓ Lengths match")
    else:
        print(f"⚠ Lengths differ: stored={len(stored_embedding_str)}, query={len(query_embedding_str)}")
    
    # Check first few values
    stored_start = stored_embedding_str[1:50]  # Skip '['
    query_start = query_embedding_str[1:50]
    
    if stored_start == query_start:
        print("✓ First values match")
    else:
        print("⚠ First values differ:")
        print(f"  Stored: {stored_start}")
        print(f"  Query:  {query_start}")
    
    print()
    
    # Test: Use stored embedding format for search
    print("Step 4: Test search with stored embedding format...")
    cursor.execute(f"""
        SELECT 
            requestid,
            text_chunk,
            1 - (embedding <=> '{stored_embedding_str}'::vector) as similarity
        FROM request_embeddings
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> '{stored_embedding_str}'::vector
        LIMIT 5;
    """)
    
    stored_search_results = cursor.fetchall()
    print(f"✓ Search with stored format: {len(stored_search_results)} results")
    if stored_search_results:
        print("  Top result similarity:", stored_search_results[0][2])
    print()
    
    # Test: Use query embedding format for search
    print("Step 5: Test search with query embedding format...")
    cursor.execute(f"""
        SELECT 
            requestid,
            text_chunk,
            1 - (embedding <=> '{query_embedding_str}'::vector) as similarity
        FROM request_embeddings
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> '{query_embedding_str}'::vector
        LIMIT 5;
    """)
    
    query_search_results = cursor.fetchall()
    print(f"✓ Search with query format: {len(query_search_results)} results")
    if query_search_results:
        print("  Top result similarity:", query_search_results[0][2])
    else:
        print("  ❌ No results - this is the problem!")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Stored embedding search: {len(stored_search_results)} results")
    print(f"Query embedding search: {len(query_search_results)} results")
    print()
    
    if len(stored_search_results) > 0 and len(query_search_results) == 0:
        print("🔴 PROBLEM IDENTIFIED:")
        print("   Query embedding format is different from stored format!")
        print("   Need to match the exact format used during insertion.")
    elif len(query_search_results) > 0:
        print("✅ Query search works! The issue was elsewhere.")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

