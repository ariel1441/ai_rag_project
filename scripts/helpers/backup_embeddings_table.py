"""
Backup request_embeddings table before regenerating embeddings.

This creates a backup table with timestamp to preserve current embeddings.
"""
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def backup_embeddings_table(silent=False):
    """
    Create a backup of the request_embeddings table.
    
    Args:
        silent: If True, don't print progress messages (for programmatic use)
        
    Returns:
        Backup table name if successful, None otherwise
    """
    if not silent:
        print("=" * 70)
        print("Backup Embeddings Table")
        print("=" * 70)
        print()
    
    # Connection details
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    
    if not password:
        if not silent:
            print("❌ ERROR: POSTGRES_PASSWORD not found in .env file")
            print("   Please add POSTGRES_PASSWORD=your_password to .env file")
        return None
    
    try:
        # Connect to database
        if not silent:
            print("Step 1: Connecting to database...")
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        if not silent:
            print(f"✓ Connected to {database} on {host}:{port}")
            print()
        
        # Check if request_embeddings table exists
        if not silent:
            print("Step 2: Checking if request_embeddings table exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'request_embeddings'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            if not silent:
                print("⚠️  WARNING: request_embeddings table does not exist!")
                print("   Nothing to backup.")
            cursor.close()
            conn.close()
            return None
        
        # Get row count
        cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
        row_count = cursor.fetchone()[0]
        if not silent:
            print(f"✓ Found request_embeddings table with {row_count:,} rows")
            print()
        
        # Create backup table name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table_name = f"request_embeddings_backup_{timestamp}"
        
        if not silent:
            print(f"Step 3: Creating backup table: {backup_table_name}...")
        
        # Create backup table with same structure
        cursor.execute(f"""
            CREATE TABLE {backup_table_name} AS
            SELECT * FROM request_embeddings;
        """)
        
        # Get backup row count
        cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name};")
        backup_count = cursor.fetchone()[0]
        
        # Create indexes on backup table (same as original)
        if not silent:
            print("Step 4: Creating indexes on backup table...")
        try:
            cursor.execute(f"""
                CREATE INDEX idx_{backup_table_name}_requestid 
                ON {backup_table_name}(requestid);
            """)
            if not silent:
                print("✓ Created index on requestid")
        except Exception as e:
            if not silent:
                print(f"⚠️  Could not create index on requestid: {e}")
        
        # Commit
        conn.commit()
        if not silent:
            print()
            print("=" * 70)
            print("✅ BACKUP COMPLETE")
            print("=" * 70)
            print(f"Backup table: {backup_table_name}")
            print(f"Rows backed up: {backup_count:,}")
            print()
            print("You can now safely regenerate embeddings.")
            print("To restore from backup, run:")
            print(f"  DROP TABLE request_embeddings;")
            print(f"  ALTER TABLE {backup_table_name} RENAME TO request_embeddings;")
            print()
        
        cursor.close()
        conn.close()
        
        return backup_table_name
        
    except psycopg2.Error as e:
        if not silent:
            print(f"❌ Database error: {e}")
        return None
    except Exception as e:
        if not silent:
            print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    backup_embeddings_table()

