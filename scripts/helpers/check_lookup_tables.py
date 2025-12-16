"""Check for lookup/reference tables in the database."""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DATABASE'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)

cur = conn.cursor()

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
""")
tables = [row[0] for row in cur.fetchall()]

print("=" * 70)
print("Database Tables Analysis")
print("=" * 70)
print(f"\nFound {len(tables)} tables:\n")
for table in tables:
    print(f"  - {table}")

# Check for potential lookup tables (common patterns)
print("\n" + "=" * 70)
print("Potential Lookup/Reference Tables:")
print("=" * 70)

lookup_patterns = ['type', 'status', 'reason', 'category', 'lookup', 'reference', 'ref', 'code', 'master']
potential_lookups = []

for table in tables:
    table_lower = table.lower()
    if any(pattern in table_lower for pattern in lookup_patterns):
        potential_lookups.append(table)
        print(f"\n📋 {table}:")
        
        # Get column info
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        print("  Columns:")
        for col_name, col_type in columns:
            print(f"    - {col_name} ({col_type})")
        
        # Get sample data
        try:
            cur.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cur.fetchall()
            if rows:
                print(f"  Sample data ({len(rows)} rows):")
                for i, row in enumerate(rows[:3], 1):
                    print(f"    Row {i}: {row}")
        except Exception as e:
            print(f"  (Could not read data: {e})")

# Check requests table for ID fields that might reference other tables
print("\n" + "=" * 70)
print("ID Fields in Requests Table (Potential Foreign Keys):")
print("=" * 70)

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'requests' 
    AND (column_name LIKE '%id' OR column_name LIKE '%Id' OR column_name LIKE '%ID')
    ORDER BY column_name
""")
id_columns = cur.fetchall()

print(f"\nFound {len(id_columns)} ID columns:\n")
for col_name, col_type in id_columns:
    print(f"  - {col_name} ({col_type})")
    
    # Check for distinct values
    try:
        cur.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM requests WHERE {col_name} IS NOT NULL")
        distinct_count = cur.fetchone()[0]
        print(f"    Distinct values: {distinct_count}")
        
        # Get sample values
        cur.execute(f"SELECT DISTINCT {col_name} FROM requests WHERE {col_name} IS NOT NULL LIMIT 5")
        sample_values = [row[0] for row in cur.fetchall()]
        print(f"    Sample values: {sample_values}")
    except Exception as e:
        print(f"    (Could not analyze: {e})")
    print()

conn.close()
print("=" * 70)
print("Analysis complete!")
print("=" * 70)

