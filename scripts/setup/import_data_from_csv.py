"""
Import data from CSV files to PostgreSQL.

This script helps you import CSV data into your Docker PostgreSQL database.
"""
import os
import sys
import psycopg2
import csv
from pathlib import Path
from dotenv import load_dotenv

def load_env():
    """Load environment variables."""
    load_dotenv()
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5433)),
        'database': os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    }

def find_csv_files():
    """Find CSV files in data/raw folder."""
    csv_dir = Path("data/raw")
    if not csv_dir.exists():
        return []
    
    csv_files = list(csv_dir.glob("*.csv"))
    return csv_files

def create_table_from_csv(conn, csv_path, table_name):
    """Create table and import data from CSV."""
    cursor = conn.cursor()
    
    print(f"   Reading CSV: {csv_path.name}")
    
    # Read first row to get columns
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Create table
        print(f"   Creating table: {table_name}")
        columns = []
        for header in headers:
            # Clean column name
            col_name = header.strip().replace(' ', '_').replace('-', '_').lower()
            # Use TEXT for all columns (safe default)
            columns.append(f'"{col_name}" TEXT')
        
        create_sql = f"""
        DROP TABLE IF EXISTS {table_name};
        CREATE TABLE {table_name} (
            {', '.join(columns)}
        );
        """
        
        cursor.execute(create_sql)
        conn.commit()
        
        # Import data
        print(f"   Importing data...")
        placeholders = ','.join(['%s'] * len(headers))
        # Clean column names for SQL
        clean_headers = []
        for h in headers:
            clean_name = h.strip().replace(" ", "_").replace("-", "_").lower()
            clean_headers.append(f'"{clean_name}"')
        column_names = ', '.join(clean_headers)
        insert_sql = f'INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})'
        
        row_count = 0
        for row in reader:
            # Pad row if needed
            while len(row) < len(headers):
                row.append(None)
            # Truncate if too long
            row = row[:len(headers)]
            
            try:
                cursor.execute(insert_sql, row)
                row_count += 1
                if row_count % 100 == 0:
                    print(f"      Imported {row_count} rows...", end='\r')
            except Exception as e:
                print(f"\n      ⚠️  Error importing row {row_count + 1}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        
        print(f"\n   ✅ Imported {row_count} rows into {table_name}")
        return row_count

def main():
    """Main import function."""
    print("=" * 80)
    print("CSV DATA IMPORT")
    print("=" * 80)
    print()
    
    # Find CSV files
    print("Looking for CSV files...")
    csv_files = find_csv_files()
    
    if not csv_files:
        print("   ❌ No CSV files found in data/raw/")
        print()
        print("To import data:")
        print("  1. Export CSV from your work PC database:")
        print("     psql -h localhost -U postgres -d ai_requests_db -c \"COPY requests TO 'requests.csv' CSV HEADER;\"")
        print()
        print("  2. Put the CSV file in: data/raw/requests.csv")
        print()
        print("  3. Run this script again")
        print()
        print("Or use the existing import script:")
        print("  python scripts/helpers/import_csv_to_postgres.py")
        return 1
    
    print(f"   ✅ Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"      - {f.name}")
    
    # Load database config
    print()
    print("Connecting to database...")
    db_config = load_env()
    
    try:
        conn = psycopg2.connect(**db_config)
        print(f"   ✅ Connected to {db_config['database']}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print()
        print("Make sure:")
        print("  1. Docker PostgreSQL is running")
        print("  2. .env file exists with correct credentials")
        return 1
    
    # Import each CSV
    print()
    print("Importing CSV files...")
    print()
    
    total_rows = 0
    for csv_file in csv_files:
        # Use filename as table name (without extension)
        table_name = csv_file.stem.lower().replace('-', '_').replace(' ', '_')
        
        try:
            rows = create_table_from_csv(conn, csv_file, table_name)
            total_rows += rows
        except Exception as e:
            print(f"   ❌ Failed to import {csv_file.name}: {e}")
            continue
    
    conn.close()
    
    print()
    print("=" * 80)
    print("IMPORT COMPLETE!")
    print("=" * 80)
    print()
    print(f"✅ Imported {total_rows} total rows")
    print()
    print("Next steps:")
    print("  1. Verify data:")
    print("     docker exec -it rag_postgres psql -U postgres -d ai_requests_db -c \"SELECT COUNT(*) FROM requests;\"")
    print()
    print("  2. Generate embeddings:")
    print("     python scripts/core/generate_embeddings.py")
    print()
    
    return 0

if __name__ == "__main__":
    exit(main())

