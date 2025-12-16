"""Check if requests exist with both person and status."""
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

# Check requests with status_id = 1
cursor.execute("""
    SELECT COUNT(DISTINCT requestid) FROM requests WHERE requeststatusid::TEXT = '1'::TEXT
""")
status_1_count = cursor.fetchone()[0]
print(f"Requests with status_id = 1: {status_1_count}")

# Check requests with "יניב ליבוביץ" in person fields
cursor.execute("""
    SELECT COUNT(DISTINCT requestid)
    FROM requests
    WHERE 
        LOWER(COALESCE(updatedby, '')) LIKE '%יניב ליבוביץ%' OR
        LOWER(COALESCE(createdby, '')) LIKE '%יניב ליבוביץ%' OR
        LOWER(COALESCE(responsibleemployeename, '')) LIKE '%יניב ליבוביץ%'
""")
person_count = cursor.fetchone()[0]
print(f"Requests with 'יניב ליבוביץ' in person fields: {person_count}")

# Check requests with BOTH
cursor.execute("""
    SELECT COUNT(DISTINCT r.requestid)
    FROM requests r
    WHERE r.requeststatusid::TEXT = '1'::TEXT
    AND (
        LOWER(COALESCE(r.updatedby, '')) LIKE '%יניב ליבוביץ%' OR
        LOWER(COALESCE(r.createdby, '')) LIKE '%יניב ליבוביץ%' OR
        LOWER(COALESCE(r.responsibleemployeename, '')) LIKE '%יניב ליבוביץ%'
    )
""")
both_count = cursor.fetchone()[0]
print(f"Requests with BOTH status_id = 1 AND 'יניב ליבוביץ': {both_count}")

# Check if text_chunk contains "יניב ליבוביץ" for status 1 requests
cursor.execute("""
    SELECT COUNT(DISTINCT e.requestid)
    FROM request_embeddings e
    INNER JOIN requests r ON e.requestid = r.requestid
    WHERE r.requeststatusid::TEXT = '1'::TEXT
    AND e.text_chunk LIKE '%יניב ליבוביץ%'
""")
text_chunk_count = cursor.fetchone()[0]
print(f"Requests with status_id = 1 AND 'יניב ליבוביץ' in text_chunk: {text_chunk_count}")

cursor.close()
conn.close()

