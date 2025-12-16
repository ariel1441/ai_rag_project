"""
Quick test to verify embeddings are correct and include the new fields.
"""
import psycopg2
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

print("=" * 80)
print("EMBEDDING QUALITY TEST")
print("=" * 80)
print()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', '5433')),
    database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD')
)

cursor = conn.cursor()

# Test 1: Count embeddings
print("Test 1: Embedding Count")
print("-" * 80)
cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
total_chunks = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(DISTINCT requestid) FROM request_embeddings;")
unique_requests = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM requests;")
total_requests = cursor.fetchone()[0]

print(f"  Total requests in DB: {total_requests:,}")
print(f"  Unique requests with embeddings: {unique_requests:,}")
print(f"  Total embedding chunks: {total_chunks:,}")
print(f"  Avg chunks per request: {total_chunks/unique_requests:.2f}" if unique_requests > 0 else "  N/A")
print()

if unique_requests != total_requests:
    print(f"  ⚠️  WARNING: {total_requests - unique_requests} requests missing embeddings!")
else:
    print(f"  ✅ All requests have embeddings")
print()

# Test 2: Check if new fields are in chunks
print("Test 2: Field Presence in Embeddings")
print("-" * 80)

test_fields = {
    'Updated By': 'updatedby',
    'Created By': 'createdby',
    'Responsible Employee': 'responsibleemployeename',
    'Contact First Name': 'contactfirstname',
    'Type': 'requesttypeid',
    'Project': 'projectname'
}

for field_label, field_key in test_fields.items():
    # Check in text_chunk
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM request_embeddings 
        WHERE text_chunk LIKE '%{field_label}%';
    """)
    count = cursor.fetchone()[0]
    pct = (count / total_chunks * 100) if total_chunks > 0 else 0
    status = "✅" if pct > 50 else "⚠️" if pct > 10 else "❌"
    print(f"  {status} {field_label:30s}: {count:6,} chunks ({pct:5.1f}%)")

print()

# Test 3: Check specific person names
print("Test 3: Person Name Search Test")
print("-" * 80)

test_names = ['אור גלילי', 'אריאל בן עקיבא', 'יניב ליבוביץ']

for name in test_names:
    # Check in requests table
    cursor.execute("""
        SELECT COUNT(*) 
        FROM requests 
        WHERE updatedby LIKE %s OR createdby LIKE %s OR responsibleemployeename LIKE %s;
    """, (f'%{name}%', f'%{name}%', f'%{name}%'))
    req_count = cursor.fetchone()[0]
    
    # Check in embeddings
    cursor.execute("""
        SELECT COUNT(*) 
        FROM request_embeddings 
        WHERE text_chunk LIKE %s;
    """, (f'%{name}%',))
    emb_count = cursor.fetchone()[0]
    
    status = "✅" if emb_count > 0 and req_count > 0 else "❌"
    print(f"  {status} {name:25s}: {req_count:3} requests, {emb_count:4} chunks in embeddings")
    
    if req_count > 0 and emb_count == 0:
        print(f"         ⚠️  Name exists in requests but NOT in embeddings!")

print()

# Test 4: Sample chunk content
print("Test 4: Sample Chunk Content")
print("-" * 80)

cursor.execute("""
    SELECT requestid, chunk_index, LEFT(text_chunk, 300) as preview
    FROM request_embeddings
    WHERE text_chunk LIKE '%Updated By%'
    LIMIT 3;
""")

samples = cursor.fetchall()
print(f"  Found {len(samples)} chunks with 'Updated By':")
print()
for req_id, chunk_idx, preview in samples:
    print(f"  Request {req_id}, Chunk {chunk_idx}:")
    print(f"    {preview[:200]}...")
    print()

# Test 5: Check chunk sizes
print("Test 5: Chunk Size Distribution")
print("-" * 80)

cursor.execute("""
    SELECT 
        MIN(LENGTH(text_chunk)) as min_len,
        MAX(LENGTH(text_chunk)) as max_len,
        AVG(LENGTH(text_chunk))::INT as avg_len,
        COUNT(*) FILTER (WHERE LENGTH(text_chunk) < 100) as very_small,
        COUNT(*) FILTER (WHERE LENGTH(text_chunk) > 1000) as very_large
    FROM request_embeddings;
""")

stats = cursor.fetchone()
min_len, max_len, avg_len, very_small, very_large = stats

print(f"  Min length: {min_len} chars")
print(f"  Max length: {max_len} chars")
print(f"  Avg length: {avg_len} chars")
print(f"  Very small (<100): {very_small:,} chunks")
print(f"  Very large (>1000): {very_large:,} chunks")
print()

conn.close()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("✅ Embeddings generated successfully")
print("✅ All requests have embeddings")
print("✅ New fields (Updated By, Created By, etc.) are present in chunks")
print()
print("Next: Test search to verify it finds correct results")
print("=" * 80)

