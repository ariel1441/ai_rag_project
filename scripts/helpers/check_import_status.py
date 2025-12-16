"""Quick check if import ran"""
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
cursor.execute('SELECT COUNT(*) FROM requests')
count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM request_embeddings')
emb_count = cursor.fetchone()[0]

print(f'Requests in DB: {count:,}')
print(f'Embeddings in DB: {emb_count:,}')
print()

if count == 1175:
    print('❌ Still has OLD data (1,175 rows)')
    print('   Import did NOT run - you need to run it!')
elif count > 8000:
    print('✅ Has NEW data (8,000+ rows)')
    print('   Import DID run successfully!')
else:
    print(f'⚠️  Unexpected count: {count}')

conn.close()

