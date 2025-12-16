"""
Check what columns exist in the requests table.
"""
import os
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
    
    # Get column names
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'requests'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    
    print("=" * 80)
    print("COLUMNS IN REQUESTS TABLE")
    print("=" * 80)
    print()
    
    if columns:
        print(f"Found {len(columns)} column(s):")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
        
        # Check for requestid variations
        print()
        col_names = [c[0].lower() for c in columns]
        if 'requestid' in col_names:
            print("✅ Found 'requestid' column")
        elif 'request_id' in col_names:
            print("⚠️  Found 'request_id' (with underscore)")
        elif 'id' in col_names:
            print("⚠️  Found 'id' column")
        else:
            print("❌ No request ID column found!")
            print("   Looking for: requestid, request_id, or id")
    else:
        print("No columns found! Table might be empty or not exist.")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")

