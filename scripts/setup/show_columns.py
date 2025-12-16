"""Quick script to show actual column names."""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', 5433)),
    database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'password'),
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM requests LIMIT 1;")
columns = [desc[0] for desc in cursor.description]

print("Actual column names in your table:")
for i, col in enumerate(columns, 1):
    print(f"{i}. {col}")

cursor.close()
conn.close()

