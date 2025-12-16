"""
Investigate why names appear in chunks but not in requests table.
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

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', '5433')),
    database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD')
)

cursor = conn.cursor()

print("=" * 80)
print("INVESTIGATING NAME MISMATCH")
print("=" * 80)
print()

# Test 1: Check "אור גלילי" in requests table
print("Test 1: 'אור גלילי' in requests table")
print("-" * 80)

name = "אור גלילי"

# Check all person-related fields
cursor.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE updatedby LIKE %s) as in_updatedby,
        COUNT(*) FILTER (WHERE createdby LIKE %s) as in_createdby,
        COUNT(*) FILTER (WHERE responsibleemployeename LIKE %s) as in_responsible,
        COUNT(*) FILTER (WHERE contactfirstname LIKE %s) as in_contactfirst,
        COUNT(*) FILTER (WHERE contactlastname LIKE %s) as in_contactlast,
        COUNT(*) FILTER (WHERE projectname LIKE %s) as in_projectname,
        COUNT(*) FILTER (WHERE projectdesc LIKE %s) as in_projectdesc
    FROM requests;
""", (f'%{name}%',) * 7)

counts = cursor.fetchone()
print(f"  In updatedby: {counts[0]}")
print(f"  In createdby: {counts[1]}")
print(f"  In responsible: {counts[2]}")
print(f"  In contactfirstname: {counts[3]}")
print(f"  In contactlastname: {counts[4]}")
print(f"  In projectname: {counts[5]}")
print(f"  In projectdesc: {counts[6]}")
print()

# Get sample requests where name appears
cursor.execute("""
    SELECT requestid, updatedby, createdby, responsibleemployeename, projectname
    FROM requests
    WHERE updatedby LIKE %s 
       OR createdby LIKE %s 
       OR responsibleemployeename LIKE %s
       OR projectname LIKE %s
    LIMIT 5;
""", (f'%{name}%',) * 4)

samples = cursor.fetchall()
if samples:
    print("  Sample requests where name appears:")
    for req_id, updatedby, createdby, responsible, projectname in samples:
        print(f"    Request {req_id}:")
        if updatedby and name in str(updatedby):
            print(f"      updatedby: {updatedby}")
        if createdby and name in str(createdby):
            print(f"      createdby: {createdby}")
        if responsible and name in str(responsible):
            print(f"      responsible: {responsible}")
        if projectname and name in str(projectname):
            print(f"      projectname: {projectname}")
else:
    print("  ⚠️  No requests found with name in person fields")
print()

# Test 2: Check "אור גלילי" in embeddings
print("Test 2: 'אור גלילי' in embeddings")
print("-" * 80)

cursor.execute("""
    SELECT COUNT(DISTINCT requestid) as unique_requests,
           COUNT(*) as total_chunks
    FROM request_embeddings
    WHERE text_chunk LIKE %s;
""", (f'%{name}%',))

emb_stats = cursor.fetchone()
print(f"  Unique requests: {emb_stats[0]}")
print(f"  Total chunks: {emb_stats[1]}")
print()

# Get sample chunks
cursor.execute("""
    SELECT requestid, chunk_index, LEFT(text_chunk, 200) as preview
    FROM request_embeddings
    WHERE text_chunk LIKE %s
    LIMIT 5;
""", (f'%{name}%',))

chunk_samples = cursor.fetchall()
if chunk_samples:
    print("  Sample chunks:")
    for req_id, chunk_idx, preview in chunk_samples:
        print(f"    Request {req_id}, Chunk {chunk_idx}:")
        # Find where name appears
        if name in preview:
            idx = preview.find(name)
            start = max(0, idx - 50)
            end = min(len(preview), idx + len(name) + 50)
            context = preview[start:end]
            print(f"      Context: ...{context}...")
        print()

# Test 3: Check "יניב ליבוביץ" - why 361 chunks for 225 requests?
print("Test 3: 'יניב ליבוביץ' - Chunk distribution")
print("-" * 80)

name2 = "יניב ליבוביץ"

cursor.execute("""
    SELECT requestid, COUNT(*) as chunk_count
    FROM request_embeddings
    WHERE text_chunk LIKE %s
    GROUP BY requestid
    ORDER BY chunk_count DESC
    LIMIT 10;
""", (f'%{name2}%',))

dist = cursor.fetchall()
print(f"  Top 10 requests by chunk count:")
total_chunks_shown = 0
for req_id, chunk_count in dist:
    print(f"    Request {req_id}: {chunk_count} chunks")
    total_chunks_shown += chunk_count

print()
print(f"  (Showing top 10, total chunks in these: {total_chunks_shown})")
print()

# Check average chunks per request
cursor.execute("""
    SELECT 
        COUNT(DISTINCT requestid) as unique_requests,
        COUNT(*) as total_chunks,
        AVG(chunk_count) as avg_chunks_per_request
    FROM (
        SELECT requestid, COUNT(*) as chunk_count
        FROM request_embeddings
        WHERE text_chunk LIKE %s
        GROUP BY requestid
    ) subq;
""", (f'%{name2}%',))

avg_stats = cursor.fetchone()
if avg_stats[0] > 0:
    print(f"  Average chunks per request: {avg_stats[2]:.2f}")
    print(f"  (225 requests × {avg_stats[2]:.2f} = ~{225 * avg_stats[2]:.0f} chunks)")
print()

# Test 4: Check if name appears in different fields in chunks
print("Test 4: Where does 'אור גלילי' appear in chunks?")
print("-" * 80)

cursor.execute("""
    SELECT requestid, chunk_index, text_chunk
    FROM request_embeddings
    WHERE text_chunk LIKE %s
    LIMIT 3;
""", (f'%{name}%',))

chunks = cursor.fetchall()
for req_id, chunk_idx, text_chunk in chunks:
    print(f"  Request {req_id}, Chunk {chunk_idx}:")
    # Find all occurrences
    if name in text_chunk:
        # Find context around name
        parts = text_chunk.split(name)
        if len(parts) > 1:
            # Show what comes before and after
            before = parts[0][-50:] if len(parts[0]) > 50 else parts[0]
            after = parts[1][:50] if len(parts[1]) > 50 else parts[1]
            print(f"    ...{before}[{name}]{after}...")
    print()

conn.close()

print("=" * 80)

