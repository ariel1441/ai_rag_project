"""
Import CSV file to PostgreSQL table.

This is a generic helper for the universal embedding setup.
Allows users to import CSV from any database (SQL Server, MySQL, etc.) to PostgreSQL.
"""
import psycopg2
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv


def detect_csv_columns(csv_path: str, sample_rows: int = 10) -> Dict:
    """
    Detect CSV structure (columns, types, sample data).
    
    Returns:
        Dict with columns, sample data, row count estimate
    """
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        # Try to detect delimiter
        sample = f.read(1024)
        f.seek(0)
        
        # Common delimiters
        delimiter = ','
        if ';' in sample and sample.count(';') > sample.count(','):
            delimiter = ';'
        elif '\t' in sample:
            delimiter = '\t'
        
        reader = csv.DictReader(f, delimiter=delimiter)
        
        # Get columns
        columns = reader.fieldnames or []
        
        # Read sample rows
        sample_data = []
        row_count = 0
        for i, row in enumerate(reader):
            if i < sample_rows:
                sample_data.append(row)
            row_count += 1
            if i >= sample_rows:
                # Count remaining rows
                row_count += sum(1 for _ in reader)
                break
        
        # Estimate types from sample data
        column_types = {}
        for col in columns:
            if sample_data:
                # Check sample values
                sample_values = [row.get(col) for row in sample_data if row.get(col)]
                if sample_values:
                    # Try to determine type
                    first_val = sample_values[0]
                    if first_val.isdigit():
                        column_types[col] = 'INTEGER'
                    elif first_val.replace('.', '', 1).isdigit():
                        column_types[col] = 'NUMERIC'
                    else:
                        column_types[col] = 'TEXT'
                else:
                    column_types[col] = 'TEXT'
            else:
                column_types[col] = 'TEXT'
        
        return {
            'columns': columns,
            'column_types': column_types,
            'sample_data': sample_data,
            'row_count': row_count,
            'delimiter': delimiter
        }


def create_table_from_csv(cursor, table_name: str, csv_info: Dict):
    """
    Create PostgreSQL table based on CSV structure.
    
    Args:
        cursor: Database cursor
        table_name: Name for new table
        csv_info: Dict from detect_csv_columns()
    """
    # Drop if exists
    cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
    
    # Build CREATE TABLE statement
    columns_def = []
    for col in csv_info['columns']:
        col_clean = col.strip().replace(' ', '_').replace('-', '_')
        col_type = csv_info['column_types'].get(col, 'TEXT')
        columns_def.append(f'"{col_clean}" {col_type}')
    
    create_sql = f"""
        CREATE TABLE {table_name} (
            {', '.join(columns_def)}
        );
    """
    
    cursor.execute(create_sql)


def import_csv_data(cursor, table_name: str, csv_path: str, csv_info: Dict, batch_size: int = 1000):
    """
    Import CSV data into PostgreSQL table.
    
    Args:
        cursor: Database cursor
        table_name: Target table name
        csv_path: Path to CSV file
        csv_info: Dict from detect_csv_columns()
    """
    from psycopg2.extras import execute_values
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=csv_info['delimiter'])
        
        # Get column names (cleaned)
        column_names = [col.strip().replace(' ', '_').replace('-', '_') for col in csv_info['columns']]
        
        batch = []
        total_imported = 0
        
        for row in reader:
            # Clean column names in row
            cleaned_row = {}
            for orig_col, clean_col in zip(csv_info['columns'], column_names):
                cleaned_row[clean_col] = row.get(orig_col, '')
            
            # Prepare values tuple
            values = tuple(cleaned_row.get(col, '') for col in column_names)
            batch.append(values)
            
            if len(batch) >= batch_size:
                # Insert batch
                placeholders = ','.join(['%s'] * len(column_names))
                insert_sql = f"""
                    INSERT INTO {table_name} ({', '.join(f'"{col}"' for col in column_names)})
                    VALUES %s
                """
                execute_values(cursor, insert_sql, batch)
                total_imported += len(batch)
                batch = []
        
        # Insert remaining
        if batch:
            placeholders = ','.join(['%s'] * len(column_names))
            insert_sql = f"""
                INSERT INTO {table_name} ({', '.join(f'"{col}"' for col in column_names)})
                VALUES %s
            """
            execute_values(cursor, insert_sql, batch)
            total_imported += len(batch)
    
    return total_imported


def import_csv_to_postgres(csv_path: str, table_name: str, connection_params: Dict = None) -> Dict:
    """
    Main function to import CSV to PostgreSQL.
    
    Args:
        csv_path: Path to CSV file
        table_name: Name for PostgreSQL table
        connection_params: Database connection params (or uses .env)
    
    Returns:
        Dict with import results
    """
    # Load .env if connection_params not provided
    if not connection_params:
        load_dotenv()
        connection_params = {
            'host': os.getenv("POSTGRES_HOST", "localhost"),
            'port': int(os.getenv("POSTGRES_PORT", "5433")),
            'database': os.getenv("POSTGRES_DATABASE"),
            'user': os.getenv("POSTGRES_USER", "postgres"),
            'password': os.getenv("POSTGRES_PASSWORD")
        }
    
    if not connection_params.get('database') or not connection_params.get('password'):
        return {'error': 'Database connection parameters missing'}
    
    # Check CSV file exists
    csv_file = Path(csv_path)
    if not csv_file.exists():
        return {'error': f'CSV file not found: {csv_path}'}
    
    print(f"Analyzing CSV file: {csv_path}")
    csv_info = detect_csv_columns(csv_path)
    
    print(f"✓ Detected {len(csv_info['columns'])} columns")
    print(f"✓ Estimated {csv_info['row_count']:,} rows")
    print()
    
    # Connect to database
    try:
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
    except Exception as e:
        return {'error': f'Cannot connect to database: {e}'}
    
    try:
        # Create table
        print(f"Creating table: {table_name}")
        create_table_from_csv(cursor, table_name, csv_info)
        conn.commit()
        print(f"✓ Table created")
        print()
        
        # Import data
        print(f"Importing data from CSV...")
        total_imported = import_csv_data(cursor, table_name, csv_path, csv_info)
        conn.commit()
        print(f"✓ Imported {total_imported:,} rows")
        print()
        
        # Verify
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        
        return {
            'success': True,
            'table_name': table_name,
            'columns': csv_info['columns'],
            'rows_imported': total_imported,
            'rows_verified': count
        }
    
    except Exception as e:
        return {'error': f'Import failed: {e}'}
    
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python import_csv_to_postgres.py <csv_path> <table_name>")
        print("Example: python import_csv_to_postgres.py data.csv my_table")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    table_name = sys.argv[2]
    
    result = import_csv_to_postgres(csv_path, table_name)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("=" * 80)
        print("✅ CSV IMPORT COMPLETE!")
        print("=" * 80)
        print(f"Table: {result['table_name']}")
        print(f"Columns: {len(result['columns'])}")
        print(f"Rows imported: {result['rows_imported']:,}")
        print(f"Rows verified: {result['rows_verified']:,}")
        print()
        print("Next step: Run embedding setup wizard")
        print("  python scripts/setup/setup_embeddings.py")
