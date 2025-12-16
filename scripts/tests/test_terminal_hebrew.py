"""
Test Hebrew display in terminal and show search results.
Run this to verify terminal encoding is fixed.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import sys

# Fix encoding for Windows - use UTF-8 and set console code page
if sys.platform == 'win32':
    try:
        import os
        # Set console to UTF-8
        os.system('chcp 65001 >nul 2>&1')
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        # Enable bidirectional text support
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 70)
print("Terminal Hebrew Display Test")
print("=" * 70)
print()

# Test 1: Display Hebrew text
print("Test 1: Hebrew Text Display")
print("-" * 70)
print("If you see Hebrew correctly, the terminal encoding is fixed!")
print()
print("Hebrew text: אלינור בדיקה")
print("English text: Elinor test")
print("Mixed: אלינור test בדיקה")
print()

# Test 2: Check database connection
print("Test 2: Database Connection")
print("-" * 70)

host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5433")
database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD")

if not password:
    print("❌ ERROR: POSTGRES_PASSWORD not in .env file!")
    print("   Create .env file with your password (see env.example.txt)")
    exit(1)

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    cursor = conn.cursor()
    print("✅ Database connection successful!")
    print()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)

# Test 3: Check data in database
print("Test 3: Check Data in Database")
print("-" * 70)

cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
total_embeddings = cursor.fetchone()[0]
print(f"Total embeddings: {total_embeddings}")

cursor.execute("SELECT COUNT(*) FROM request_embeddings WHERE text_chunk LIKE '%אלינור%';")
elior_count = cursor.fetchone()[0]
print(f"Embeddings with 'אלינור': {elior_count}")
print()

# Test 4: Show sample data
print("Test 4: Sample Data (Hebrew Text)")
print("-" * 70)
cursor.execute("""
    SELECT requestid, LEFT(text_chunk, 100) as text_preview
    FROM request_embeddings 
    WHERE text_chunk LIKE '%אלינור%'
    LIMIT 5;
""")

samples = cursor.fetchall()
print("Sample requests with 'אלינור':")
for i, (req_id, text_preview) in enumerate(samples, 1):
    print(f"  {i}. Request {req_id}:")
    print(f"     {text_preview}")
    print()

# Test 5: Test vector search (simplified)
print("Test 5: Vector Search Test")
print("-" * 70)
print("Generating embedding for 'אלינור'...")

try:
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query = "אלינור"
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    # Format exactly like insertion
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    print(f"✅ Embedding generated: {len(query_embedding)} dimensions")
    print()
    
    # Try search using existing embeddings (cross join)
    print("Testing search using existing embeddings...")
    cursor.execute("""
        SELECT 
            e1.requestid as source_id,
            e2.requestid as similar_id,
            LEFT(e2.text_chunk, 100) as text_preview,
            1 - (e1.embedding <=> e2.embedding) as similarity
        FROM request_embeddings e1
        CROSS JOIN request_embeddings e2
        WHERE e1.text_chunk LIKE '%אלינור%'
          AND e2.text_chunk LIKE '%אלינור%'
          AND e1.requestid != e2.requestid
        ORDER BY e1.embedding <=> e2.embedding
        LIMIT 5;
    """)
    
    cross_results = cursor.fetchall()
    
    if cross_results:
        print(f"✅ Found {len(cross_results)} similar embeddings!")
        print()
        print("Similar requests (using existing embeddings):")
        for i, (source_id, similar_id, text_preview, similarity) in enumerate(cross_results, 1):
            print(f"  {i}. Request {similar_id} (similarity: {similarity:.4f})")
            print(f"     {text_preview}")
            print()
    else:
        print("⚠ No results from cross-join search")
        print("   This might indicate a pgvector issue")
        print()
    
    # Now try with query embedding
    print("Testing search with query embedding...")
    search_sql = f"""
        SELECT 
            requestid,
            chunk_index,
            LEFT(text_chunk, 100) as text_preview,
            1 - (embedding <=> '{embedding_str}'::vector) as similarity
        FROM request_embeddings
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT 5;
    """
    
    cursor.execute(search_sql)
    query_results = cursor.fetchall()
    
    if query_results:
        print(f"✅ Found {len(query_results)} results with query embedding!")
        print()
        print("Top results:")
        for i, (req_id, chunk_idx, text_preview, similarity) in enumerate(query_results, 1):
            has_elior = 'אלינור' in text_preview
            marker = "✓" if has_elior else " "
            print(f"  {i}. {marker} Request {req_id} (similarity: {similarity:.4f})")
            print(f"     {text_preview}")
            print()
    else:
        print("❌ No results with query embedding")
        print("   This is the issue we need to fix")
        print()
    
except Exception as e:
    print(f"❌ Error during search: {e}")
    import traceback
    traceback.print_exc()

conn.close()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("✅ Terminal encoding: Check if Hebrew displays correctly above")
print(f"✅ Database connection: Working")
print(f"✅ Data exists: {total_embeddings} embeddings, {elior_count} with 'אלינור'")
if cross_results:
    print("✅ Vector operations: Working (cross-join search works)")
else:
    print("❌ Vector operations: May have issues")
if query_results:
    print("✅ Query search: Working!")
else:
    print("❌ Query search: Not working (needs fix)")
print()
print("=" * 70)

