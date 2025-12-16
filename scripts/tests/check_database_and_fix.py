"""Check database and fix name extraction issue"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', '5433')),
    database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD')
)
cursor = conn.cursor()

print("="*80)
print("DATABASE CHECK")
print("="*80)
print()

# Check for יניב ליבוביץ
print("1. Checking for 'יניב ליבוביץ' in database:")
cursor.execute("SELECT requestid, updatedby, projectname FROM requests WHERE updatedby LIKE %s LIMIT 10", ('%יניב ליבוביץ%',))
results = cursor.fetchall()
print(f"   Found {len(results)} requests (showing first 10):")
for r in results:
    print(f"   Request {r[0]}: {r[1]} - {r[2]}")
print()

# Check Request ID range
cursor.execute("SELECT MIN(requestid), MAX(requestid), COUNT(*) FROM requests")
min_id, max_id, count = cursor.fetchone()
print(f"2. Database statistics:")
print(f"   Total requests: {count}")
print(f"   Request ID range: {min_id} to {max_id}")
print()

# Check embeddings
cursor.execute("SELECT COUNT(*) FROM request_embeddings")
emb_count = cursor.fetchone()[0]
print(f"3. Embeddings:")
print(f"   Total embeddings: {emb_count}")
print()

# Check if we can find יניב ליבוביץ in embeddings
cursor.execute("""
    SELECT DISTINCT e.requestid, r.updatedby, r.projectname
    FROM request_embeddings e
    INNER JOIN requests r ON e.requestid = r.requestid
    WHERE e.text_chunk LIKE %s
    LIMIT 10
""", ('%יניב ליבוביץ%',))
results = cursor.fetchall()
print(f"4. Finding 'יניב ליבוביץ' in embeddings:")
print(f"   Found {len(results)} requests:")
for r in results:
    print(f"   Request {r[0]}: {r[1]} - {r[2]}")
print()

conn.close()

