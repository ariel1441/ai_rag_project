"""
Check what tables exist in Docker PostgreSQL.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5433)),
        database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'password'),
    )
    
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    
    print("=" * 80)
    print("TABLES IN DATABASE")
    print("=" * 80)
    print()
    
    if tables:
        print(f"Found {len(tables)} table(s):")
        for table in tables:
            table_name = table[0]
            # Get row count
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
    else:
        print("No tables found!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")

