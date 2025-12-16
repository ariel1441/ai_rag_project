"""Check all tables in PostgreSQL database and their row counts"""
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

print("=" * 80)
print("POSTGRESQL DATABASE STATUS")
print("=" * 80)
print()

# Get all tables
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")

tables = cursor.fetchall()

print(f"Found {len(tables)} tables:")
print()

for table_name, in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
        count = cursor.fetchone()[0]
        
        # Get table size
        cursor.execute(f"""
            SELECT pg_size_pretty(pg_total_relation_size('"{table_name}"'));
        """)
        size = cursor.fetchone()[0]
        
        print(f"  📊 {table_name:40s} | {count:8,} rows | {size}")
        
        # If it's requests or request_embeddings, show sample
        if table_name.lower() in ['requests', 'request_embeddings']:
            cursor.execute(f'SELECT column_name FROM information_schema.columns WHERE table_name = \'{table_name}\' LIMIT 5;')
            cols = cursor.fetchall()
            col_names = [c[0] for c in cols]
            print(f"      Columns: {', '.join(col_names[:5])}...")
            
    except Exception as e:
        print(f"  ❌ {table_name:40s} | Error: {e}")

print()
print("=" * 80)
print("DETAILED TABLE INFO")
print("=" * 80)
print()

# Check requests table specifically
if any('requests' in t[0].lower() for t in tables):
    print("REQUESTS TABLE(S):")
    print()
    for table_name, in tables:
        if 'request' in table_name.lower() and 'embedding' not in table_name.lower():
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            count = cursor.fetchone()[0]
            
            # Get column count
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}';
            """)
            col_count = cursor.fetchone()[0]
            
            # Get sample request IDs
            try:
                cursor.execute(f'SELECT requestid FROM "{table_name}" ORDER BY requestid LIMIT 5;')
                sample_ids = cursor.fetchall()
                ids_str = ', '.join([str(r[0]) for r in sample_ids])
            except:
                ids_str = "N/A"
            
            print(f"  Table: {table_name}")
            print(f"    Rows: {count:,}")
            print(f"    Columns: {col_count}")
            print(f"    Sample IDs: {ids_str}")
            print()

# Check embeddings table
if any('embedding' in t[0].lower() for t in tables):
    print("EMBEDDINGS TABLE(S):")
    print()
    for table_name, in tables:
        if 'embedding' in table_name.lower():
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            count = cursor.fetchone()[0]
            
            # Get unique request IDs
            try:
                cursor.execute(f'SELECT COUNT(DISTINCT requestid) FROM "{table_name}";')
                unique_reqs = cursor.fetchone()[0]
                print(f"  Table: {table_name}")
                print(f"    Total chunks: {count:,}")
                print(f"    Unique requests: {unique_reqs:,}")
                print(f"    Avg chunks per request: {count/unique_reqs:.2f}" if unique_reqs > 0 else "    Avg chunks: N/A")
                print()
            except Exception as e:
                print(f"  Table: {table_name}")
                print(f"    Rows: {count:,}")
                print(f"    Error getting details: {e}")
                print()

conn.close()

print("=" * 80)

