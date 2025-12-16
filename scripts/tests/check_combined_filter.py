"""Check if requests exist with both filters."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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

# Check requests with type_id = 4
cursor.execute("""
    SELECT COUNT(DISTINCT requestid) FROM requests WHERE requesttypeid::TEXT = '4'::TEXT
""")
type_4_count = cursor.fetchone()[0]
print(f"Requests with type_id = 4: {type_4_count}")

# Check requests with "אור גלילי" in projectname
cursor.execute("""
    SELECT COUNT(DISTINCT requestid) FROM requests WHERE projectname LIKE '%אור גלילי%'
""")
or_galili_count = cursor.fetchone()[0]
print(f"Requests with 'אור גלילי' in projectname: {or_galili_count}")

# Check requests with BOTH
cursor.execute("""
    SELECT COUNT(DISTINCT r.requestid)
    FROM requests r
    WHERE r.requesttypeid::TEXT = '4'::TEXT
    AND r.projectname LIKE '%אור גלילי%'
""")
both_count = cursor.fetchone()[0]
print(f"Requests with BOTH type_id = 4 AND 'אור גלילי': {both_count}")

# Check if text_chunk contains "אור גלילי" for type 4 requests
cursor.execute("""
    SELECT COUNT(DISTINCT e.requestid)
    FROM request_embeddings e
    INNER JOIN requests r ON e.requestid = r.requestid
    WHERE r.requesttypeid::TEXT = '4'::TEXT
    AND e.text_chunk LIKE '%אור גלילי%'
""")
text_chunk_count = cursor.fetchone()[0]
print(f"Requests with type_id = 4 AND 'אור גלילי' in text_chunk: {text_chunk_count}")

cursor.close()
conn.close()

