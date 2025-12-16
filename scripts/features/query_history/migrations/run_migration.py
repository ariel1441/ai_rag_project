"""
Run Query History Migration

This script applies the database migration for query history feature.
Can be safely run multiple times (uses IF NOT EXISTS).
"""
import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Run the migration script."""
    # Get migration file
    migration_file = Path(__file__).parent / "001_create_query_history_tables.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    # Read migration SQL
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Connect to database
    try:
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        if not password:
            print("❌ POSTGRES_PASSWORD not set in .env")
            return False
        
        print(f"Connecting to database: {database}@{host}:{port}")
        conn = psycopg2.connect(
            host=host, port=int(port), database=database,
            user=user, password=password
        )
        cursor = conn.cursor()
        
        print("Running migration...")
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration completed successfully!")
        
        # Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('user_query_history', 'query_statistics')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Created tables: {', '.join(tables)}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

