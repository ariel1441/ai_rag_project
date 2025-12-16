"""Debug what's in text_chunk for requests."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from dotenv import load_dotenv
import psycopg2
from pgvector.psycopg2 import register_vector

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5433")),
    database=os.getenv("POSTGRES_DATABASE", "ai_requests_db"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD")
)
register_vector(conn)
cursor = conn.cursor()

# Check requests with "אור גלילי" in projectname
cursor.execute("""
    SELECT DISTINCT e.requestid, e.text_chunk, r.projectname
    FROM request_embeddings e
    INNER JOIN requests r ON e.requestid = r.requestid
    WHERE r.projectname LIKE '%אור גלילי%'
    LIMIT 5
""")

print("Sample text_chunks for requests with 'אור גלילי' in projectname:")
print("=" * 80)
for row in cursor.fetchall():
    req_id, text_chunk, projectname = row
    print(f"\nRequestID: {req_id}")
    print(f"ProjectName: {projectname}")
    print(f"TextChunk (first 200 chars): {text_chunk[:200] if text_chunk else 'None'}...")
    print(f"Contains 'אור גלילי': {'אור גלילי' in (text_chunk or '')}")

cursor.close()
conn.close()

