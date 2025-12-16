"""
Backup the current request_embeddings table before regenerating with new fields.
"""
import psycopg2
import os
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 80)
print("BACKUP EMBEDDINGS TABLE")
print("=" * 80)
print()

# Connection
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5433")
database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD")

if not password:
    print("ERROR: POSTGRES_PASSWORD not in .env!")
    exit(1)

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    cursor = conn.cursor()
    
    # Check current count
    print("Step 1: Checking current embeddings...")
    cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
    current_count = cursor.fetchone()[0]
    print(f"  Current embeddings: {current_count:,}")
    print()
    
    if current_count == 0:
        print("⚠️ No embeddings to backup! Table is empty.")
        print("  You can proceed with regeneration.")
        conn.close()
        exit(0)
    
    # Create backup table name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_table = f"request_embeddings_backup_{timestamp}"
    
    print(f"Step 2: Creating backup table: {backup_table}")
    print()
    
    # Create backup table (copy structure and data)
    cursor.execute(f"""
        CREATE TABLE {backup_table} AS 
        SELECT * FROM request_embeddings;
    """)
    
    # Verify backup
    cursor.execute(f"SELECT COUNT(*) FROM {backup_table};")
    backup_count = cursor.fetchone()[0]
    
    conn.commit()
    
    print(f"✓ Backup created successfully!")
    print(f"  Backup table: {backup_table}")
    print(f"  Records backed up: {backup_count:,}")
    print()
    
    # Show backup table info
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT requestid) as unique_requests,
            MIN(created_at) as oldest,
            MAX(created_at) as newest
        FROM {backup_table};
    """)
    info = cursor.fetchone()
    total, unique_requests, oldest, newest = info
    
    print("Backup summary:")
    print(f"  Total embeddings: {total:,}")
    print(f"  Unique requests: {unique_requests:,}")
    print(f"  Oldest: {oldest}")
    print(f"  Newest: {newest}")
    print()
    
    print("=" * 80)
    print("✅ BACKUP COMPLETE!")
    print("=" * 80)
    print()
    print("You can now safely regenerate embeddings.")
    print("To restore from backup, run:")
    print(f"  TRUNCATE TABLE request_embeddings;")
    print(f"  INSERT INTO request_embeddings SELECT * FROM {backup_table};")
    print()
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("=" * 80)

